# Copyright 2016 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from copy import deepcopy
import os

import jsonpatch
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import timeutils
from oslo_utils import uuidutils

from glare.common import exception
from glare.common import policy
from glare.common import store_api
from glare.common import utils
from glare.db import artifact_api
from glare.i18n import _
from glare import locking
from glare.notification import Notifier
from glare.objects.meta import registry

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Engine(object):
    """Engine is responsible for executing different helper operations when
    processing incoming requests from Glare API.

    Engine receives incoming data and does the following:
     - check basic policy permissions;
     - requests artifact definition from artifact type registry;
     - check access permission(ro, rw);
     - lock artifact for update if needed;
     - pass data to base artifact to execute all business logic operations
       with database;
     - notify other users about finished operation.

    Engine should not include any business logic and validation related
    to Artifacts. Engine should not know any internal details of artifact
    type, because this part of the work is done by Base artifact type.
    """
    def __init__(self):
        # register all artifact types
        registry.ArtifactRegistry.register_all_artifacts()

        # generate all schemas
        self.schemas = {}
        for name, type_list in registry.ArtifactRegistry.obj_classes().items():
            type_name = type_list[0].get_type_name()
            self.schemas[type_name] = registry.ArtifactRegistry.\
                get_artifact_type(type_name).gen_schemas()

    lock_engine = locking.LockEngine(artifact_api.ArtifactLockApi())

    def _create_scoped_lock(self, context, type_name, name, version,
                            owner, visibility='private'):
        """Create scoped lock for artifact."""
        # validate that artifact doesn't exist for the scope
        filters = [('name', 'eq:' + name), ('version', 'eq:' + version)]
        if visibility == 'public':
            filters.extend([('visibility', 'public')])
        elif visibility == 'private':
            filters.extend([('owner', 'eq:' + owner),
                            ('visibility', 'private')])

        scope_id = "%s:%s:%s" % (type_name, name, version)
        if visibility != 'public':
            scope_id += ':%s' % owner
        lock = self.lock_engine.acquire(context, scope_id)

        try:
            if len(self.list(context, type_name, filters)) > 0:
                msg = _("Artifact with this name and version is already "
                        "exists for this scope.")
                raise exception.Conflict(msg)
        except Exception:
            with excutils.save_and_reraise_exception(logger=LOG):
                self.lock_engine.release(lock)

        return lock

    @staticmethod
    def _show_artifact(ctx, type_name, artifact_id, read_only=False):
        """Return artifact requested by user.

        Check access permissions and policies.

        :param ctx: user context
        :param type_name: artifact type name
        :param artifact_id: id of the artifact to be updated
        :param read_only: flag, if set to True only read access is checked,
         if False then engine checks if artifact can be modified by the user
        """
        artifact_type = registry.ArtifactRegistry.get_artifact_type(type_name)
        # only artifact is available for class users
        af = artifact_type.show(ctx, artifact_id)
        if not read_only:
            if not ctx.is_admin and ctx.tenant != af.owner or ctx.read_only:
                raise exception.Forbidden()
            LOG.debug("Artifact %s acquired for read-write access",
                      artifact_id)
        else:
            LOG.debug("Artifact %s acquired for read-only access", artifact_id)

        return af

    def show_type_schemas(self, context, type_name=None):
        policy.authorize("artifact:type_list", {}, context)
        if type_name is None:
            return self.schemas
        if type_name not in self.schemas:
            msg = _("Artifact type %s does not exist") % type_name
            raise exception.NotFound(message=msg)
        return self.schemas[type_name]

    def _apply_patch(self, context, af, patch):
        # This function is a collection of hacks and workarounds to make
        # json patch apply changes to oslo_vo object.
        action_names = {'artifact:update'}
        af_dict = af.to_dict()
        try:
            for operation in patch._ops:
                # apply the change to make sure that it's correct
                af_dict = operation.apply(af_dict)

                # format of location is "/key/value" or just "/key"
                # first case symbolizes that we have dict or list insertion,
                # second, that we work with a field itself.
                items = operation.location.split('/', 2)
                field_name = items[1]
                if af.is_blob(field_name) or af.is_blob_dict(field_name):
                    msg = _("Cannot add blob with this request. "
                            "Use special Blob API for that.")
                    raise exception.BadRequest(msg)
                if len(items) == 2 and operation.operation['op'] == 'remove':
                    msg = _("Cannot remove field '%s' from "
                            "artifact.") % field_name
                    raise exception.BadRequest(msg)

                # work with hooks and define action names
                if field_name == 'visibility':
                    utils.validate_visibility_transition(
                        af,
                        from_visibility=af.visibility,
                        to_visibility=af_dict['visibility']
                    )
                    if af_dict['visibility'] == 'public':
                        af.validate_publish(context, af)
                        action_names.add('artifact:publish')
                elif field_name == 'status':
                    utils.validate_status_transition(
                        af, from_status=af.status, to_status=af_dict['status'])
                    if af_dict['status'] == 'deactivated':
                        action_names.add('artifact:deactivate')
                    elif af_dict['status'] == 'active':
                        if af.status == 'deactivated':
                            action_names.add('artifact:reactivate')
                        else:
                            af.validate_activate(context, af)
                            action_names.add('artifact:activate')
                else:
                    utils.validate_change_allowed(af, field_name)

                old_val = getattr(af, field_name)
                setattr(af, field_name, af_dict[field_name])
                new_val = getattr(af, field_name)
                if new_val == old_val:
                    # No need to save value to db if it's not changed
                    af.obj_reset_changes([field_name])

        except (jsonpatch.JsonPatchException,
                jsonpatch.JsonPointerException, TypeError) as e:
            raise exception.BadRequest(message=str(e))

        return action_names

    def create(self, context, type_name, values):
        """Create artifact record in Glare.

        :param context: user context
        :param type_name: artifact type name
        :param values: dict with artifact fields
        :return: dict representation of created artifact
        """
        action_name = "artifact:create"
        policy.authorize(action_name, values, context)
        artifact_type = registry.ArtifactRegistry.get_artifact_type(type_name)
        version = values.get('version', artifact_type.DEFAULT_ARTIFACT_VERSION)
        init_values = {
            'id': uuidutils.generate_uuid(),
            'name': values.pop('name'),
            'version': version,
            'owner': context.tenant,
            'created_at': timeutils.utcnow(),
            'updated_at': timeutils.utcnow()
        }
        af = artifact_type.init_artifact(context, init_values)
        # acquire scoped lock and execute artifact create
        with self._create_scoped_lock(context, type_name, af.name,
                                      af.version, context.tenant):
            for field_name, value in values.items():
                if af.is_blob(field_name) or af.is_blob_dict(field_name):
                    msg = _("Cannot add blob with this request. "
                            "Use special Blob API for that.")
                    raise exception.BadRequest(msg)
                utils.validate_change_allowed(af, field_name)
                setattr(af, field_name, value)
            af = af.create(context)
            # notify about new artifact
            Notifier.notify(context, action_name, af)
            # return artifact to the user
            return af.to_dict()

    def save(self, context, type_name, artifact_id, patch):
        """Update artifact with json patch.

        Apply patch to artifact and validate artifact before updating it
        in database. If there is request for visibility or status change
        then call specific method for that.

        :param context: user context
        :param type_name: name of artifact type
        :param artifact_id: id of the artifact to be updated
        :param patch: json patch object
        :return: dict representation of updated artifact
        """
        lock_key = "%s:%s" % (type_name, artifact_id)
        with self.lock_engine.acquire(context, lock_key):
            af = self._show_artifact(context, type_name, artifact_id)
            af.obj_reset_changes()
            action_names = self._apply_patch(context, af, patch)
            updates = af.obj_changes_to_primitive()

            LOG.debug("Update diff successfully calculated for artifact "
                      "%(af)s %(diff)s", {'af': artifact_id, 'diff': updates})
            if not updates:
                return af.to_dict()

            for action_name in action_names:
                policy.authorize(action_name, af.to_dict(), context)

            if any(i in updates for i in ('name', 'version', 'visibility')):
                # to change an artifact scope it's required to set a lock first
                with self._create_scoped_lock(
                        context, type_name, updates.get('name', af.name),
                        updates.get('version', af.version), af.owner,
                        updates.get('visibility', af.visibility)):
                    modified_af = af.save(context)
            else:
                modified_af = af.save(context)

            for action_name in action_names:
                Notifier.notify(context, action_name, modified_af)
            return modified_af.to_dict()

    def show(self, context, type_name, artifact_id):
        """Show detailed artifact info.

        :param context: user context
        :param type_name: Artifact type name
        :param artifact_id: id of artifact to show
        :return: definition of requested artifact
        """
        policy.authorize("artifact:get", {}, context)
        af = self._show_artifact(context, type_name, artifact_id,
                                 read_only=True)
        return af.to_dict()

    @staticmethod
    def list(context, type_name, filters, marker=None, limit=None,
             sort=None, latest=False):
        """Return list of artifacts requested by user.

        :param context: user context
        :param type_name: Artifact type name
        :param filters: filters that need to be applied to artifact
        :param marker: the artifact that considered as begin of the list
         so all artifacts before marker (including marker itself) will not be
         added to artifact list
        :param limit: maximum number of items in list
        :param sort: sorting options
        :param latest: flag that indicates, that only artifacts with highest
         versions should be returned in output
        :return: list of artifact definitions
        """
        policy.authorize("artifact:list", {}, context)
        artifact_type = registry.ArtifactRegistry.get_artifact_type(type_name)
        # return list to the user
        af_list = [af.to_dict()
                   for af in artifact_type.list(context, filters, marker,
                                                limit, sort, latest)]
        return af_list

    @staticmethod
    def _delete_blobs(context, af, blobs):
        for name, blob in blobs.items():
            if af.is_blob(name):
                if not blob['external']:
                    try:
                        store_api.delete_blob(blob['url'], context=context)
                    except exception.NotFound:
                        # data has already been removed
                        pass
                af.db_api.update_blob(context, af.id, {name: None})
            elif af.is_blob_dict(name):
                upd_blob = deepcopy(blob)
                for key, val in blob.items():
                    if not val['external']:
                        try:
                            store_api.delete_blob(val['url'], context=context)
                        except exception.NotFound:
                            pass
                    del upd_blob[key]
                    af.db_api.update_blob(context, af.id, {name: upd_blob})

    def delete(self, context, type_name, artifact_id):
        """Delete artifact from Glare.

        :param context: User context
        :param type_name: Artifact type name
        :param artifact_id: id of artifact to delete
        """
        af = self._show_artifact(context, type_name, artifact_id)
        action_name = 'artifact:delete'
        policy.authorize(action_name, af.to_dict(), context)
        af.validate_delete(context, af)
        blobs = af.delete(context, af)

        delayed_delete = getattr(
            CONF, 'artifact_type:' + type_name).delayed_delete
        # use global parameter if delayed delete isn't set per artifact type
        if delayed_delete is None:
            delayed_delete = CONF.delayed_delete

        if not delayed_delete:
            if blobs:
                # delete blobs one by one
                self._delete_blobs(context, af, blobs)
                LOG.info("Blobs successfully deleted for artifact %s", af.id)
            # delete artifact itself
            af.db_api.delete(context, af.id)
        Notifier.notify(context, action_name, af)

    @staticmethod
    def _get_blob_info(af, field_name, blob_key=None):
        """Return requested blob info"""
        if blob_key:
            if not af.is_blob_dict(field_name):
                msg = _("%s is not a blob dict") % field_name
                raise exception.BadRequest(msg)
            return getattr(af, field_name).get(blob_key)
        else:
            if not af.is_blob(field_name):
                msg = _("%s is not a blob") % field_name
                raise exception.BadRequest(msg)
            return getattr(af, field_name, None)

    @staticmethod
    def _save_blob_info(context, af, field_name, blob_key, value):
        """Save blob instance in database."""
        if blob_key is not None:
            # Insert blob value in the folder
            folder = getattr(af, field_name)
            if value is not None:
                folder[blob_key] = value
            else:
                del folder[blob_key]
            value = folder
        return af.update_blob(context, af.id, field_name, value)

    def add_blob_location(self, context, type_name, artifact_id, field_name,
                          location, blob_meta, blob_key=None):
        """Add external location to blob.

        :param context: user context
        :param type_name: name of artifact type
        :param artifact_id: id of the artifact to be updated
        :param field_name: name of blob or blob dict field
        :param location: external blob url
        :param blob_meta: dictionary containing blob metadata like md5 checksum
        :param blob_key: if field_name is blob dict it specifies key
         in this dict
        :return: dict representation of updated artifact
        """
        blob_name = "%s[%s]" % (field_name, blob_key)\
            if blob_key else field_name

        blob = {'url': location, 'size': None, 'md5': blob_meta.get("md5"),
                'sha1': blob_meta.get("sha1"), 'id': uuidutils.generate_uuid(),
                'sha256': blob_meta.get("sha256"), 'status': 'active',
                'external': True, 'content_type': None}

        lock_key = "%s:%s" % (type_name, artifact_id)
        with self.lock_engine.acquire(context, lock_key):
            af = self._show_artifact(context, type_name, artifact_id)
            action_name = 'artifact:set_location'
            policy.authorize(action_name, af.to_dict(), context)
            if self._get_blob_info(af, field_name, blob_key):
                msg = _("Blob %(blob)s already exists for artifact "
                        "%(af)s") % {'blob': field_name, 'af': af.id}
                raise exception.Conflict(message=msg)
            utils.validate_change_allowed(af, field_name)
            modified_af = self._save_blob_info(
                context, af, field_name, blob_key, blob)

        LOG.info("External location %(location)s has been created "
                 "successfully for artifact %(artifact)s blob %(blob)s",
                 {'location': location, 'artifact': af.id,
                  'blob': blob_name})

        Notifier.notify(context, action_name, modified_af)
        return modified_af.to_dict()

    @staticmethod
    def _calculate_allowed_space(context, af, field_name, content_length=None,
                                 blob_key=None):
        """Calculate the maximum amount of data user can upload to a blob."""
        # As a default we take the maximum blob size
        max_allowed_size = af.get_max_blob_size(field_name)

        if blob_key is not None:
            # For folders we also compare it with the maximum folder size
            blobs_dict = getattr(af, field_name)
            overall_folder_size = sum(
                blob["size"] for blob in blobs_dict.values()
                if blob["size"] is not None)
            max_folder_size_allowed = af.get_max_folder_size(
                field_name) - overall_folder_size  # always non-negative
            max_allowed_size = min(max_allowed_size,
                                   max_folder_size_allowed)

        if content_length is None:
            # if no content_length was provided we have to allocate
            # all allowed space for the blob
            size = max_allowed_size
        else:
            if content_length > max_allowed_size:
                raise exception.RequestEntityTooLarge()
            size = content_length

        return size

    def upload_blob(self, context, type_name, artifact_id, field_name, fd,
                    content_type, content_length=None, blob_key=None):
        """Upload Artifact blob.

        :param context: user context
        :param type_name: name of artifact type
        :param artifact_id: id of the artifact to be updated
        :param field_name: name of blob or blob dict field
        :param fd: file descriptor that Glare uses to upload the file
        :param content_type: data content-type
        :param content_length: amount of data user wants to upload
        :param blob_key: if field_name is blob dict it specifies key
         in this dictionary
        :return: dict representation of updated artifact
        """

        blob_name = "%s[%s]" % (field_name, blob_key) \
            if blob_key else field_name
        blob_id = uuidutils.generate_uuid()

        lock_key = "%s:%s" % (type_name, artifact_id)
        with self.lock_engine.acquire(context, lock_key):
            af = self._show_artifact(context, type_name, artifact_id)
            action_name = "artifact:upload"
            policy.authorize(action_name, af.to_dict(), context)

            # create an an empty blob instance in db with 'saving' status
            if self._get_blob_info(af, field_name, blob_key):
                msg = _("Blob %(blob)s already exists for artifact "
                        "%(af)s") % {'blob': field_name, 'af': af.id}
                raise exception.Conflict(message=msg)
            utils.validate_change_allowed(af, field_name)
            size = self._calculate_allowed_space(
                context, af, field_name, content_length, blob_key)
            blob = {'url': None, 'size': size, 'md5': None, 'sha1': None,
                    'sha256': None, 'id': blob_id, 'status': 'saving',
                    'external': False, 'content_type': content_type}

            modified_af = self._save_blob_info(
                context, af, field_name, blob_key, blob)

        LOG.debug("Parameters validation for artifact %(artifact)s blob "
                  "upload passed for blob %(blob_name)s. "
                  "Start blob uploading to backend.",
                  {'artifact': af.id, 'blob_name': blob_name})

        # try to perform blob uploading to storage
        path = None
        try:
            try:
                # call upload hook first
                fd, path = af.validate_upload(context, af, field_name, fd)
            except exception.GlareException:
                raise
            except Exception as e:
                raise exception.BadRequest(message=str(e))

            default_store = getattr(
                CONF, 'artifact_type:' + type_name).default_store
            # use global parameter if default store isn't set per artifact type
            if default_store is None:
                default_store = CONF.glance_store.default_store

            location_uri, size, checksums = store_api.save_blob_to_store(
                blob_id, fd, context, size,
                store_type=default_store)
        except Exception:
            # if upload failed remove blob from db and storage
            with excutils.save_and_reraise_exception(logger=LOG):
                if blob_key is None:
                    af.update_blob(context, af.id, field_name, None)
                else:
                    blob_dict_attr = getattr(modified_af, field_name)
                    del blob_dict_attr[blob_key]
                    af.update_blob(context, af.id, field_name, blob_dict_attr)
        finally:
            if path:
                os.remove(path)

        LOG.info("Successfully finished blob uploading for artifact "
                 "%(artifact)s blob field %(blob)s.",
                 {'artifact': af.id, 'blob': blob_name})

        # update blob info and activate it
        blob.update({'url': location_uri,
                     'status': 'active',
                     'size': size})
        blob.update(checksums)

        with self.lock_engine.acquire(context, lock_key):
            af = af.show(context, artifact_id)
            modified_af = self._save_blob_info(
                context, af, field_name, blob_key, blob)

        Notifier.notify(context, action_name, modified_af)
        return modified_af.to_dict()

    def download_blob(self, context, type_name, artifact_id, field_name,
                      blob_key=None):
        """Download binary data from Glare Artifact.

        :param context: user context
        :param type_name: name of artifact type
        :param artifact_id: id of the artifact to be updated
        :param field_name: name of blob or blob dict field
        :param blob_key: if field_name is blob dict it specifies key
         in this dict
        :return: file iterator for requested file
        """
        af = self._show_artifact(context, type_name, artifact_id,
                                 read_only=True)
        policy.authorize("artifact:download", af.to_dict(), context)

        blob_name = "%s[%s]" % (field_name, blob_key)\
            if blob_key else field_name

        if af.status == 'deleted':
            msg = _("Cannot download data when artifact is deleted")
            raise exception.Forbidden(message=msg)

        blob = self._get_blob_info(af, field_name, blob_key)
        if blob is None:
            msg = _("No data found for blob %s") % blob_name
            raise exception.NotFound(message=msg)
        if blob['status'] != 'active':
            msg = _("%s is not ready for download") % blob_name
            raise exception.Conflict(message=msg)

        meta = {'md5': blob.get('md5'),
                'sha1': blob.get('sha1'),
                'sha256': blob.get('sha256'),
                'external': blob.get('external')}
        if blob['external']:
            data = {'url': blob['url']}
        else:
            data = store_api.load_from_store(uri=blob['url'], context=context)
            meta['size'] = blob.get('size')
            meta['content_type'] = blob.get('content_type')

        path = None
        try:
            # call download hook in the end
            data, path = af.validate_download(
                context, af, field_name, data)
        except exception.GlareException:
            raise
        except Exception as e:
            raise exception.BadRequest(message=str(e))
        finally:
            if path:
                os.remove(path)

        return data, meta

    def delete_blob(self, context, type_name, artifact_id, field_name,
                    blob_key=None):
        """Delete artifact blob with external location.

        :param context: user context
        :param type_name: name of artifact type
        :param artifact_id: id of artifact with the blob to delete
        :param field_name: name of blob or blob dict field
        :param blob_key: if field_name is blob dict it specifies key
         in this dictionary
        """
        af = self._show_artifact(context, type_name, artifact_id)
        action_name = 'artifact:delete_blob'
        policy.authorize(action_name, af.to_dict(), context)

        blob_name = "%s[%s]" % (field_name, blob_key)\
            if blob_key else field_name

        blob = self._get_blob_info(af, field_name, blob_key)
        if blob is None:
            msg = _("Blob %s wasn't found for artifact") % blob_name
            raise exception.NotFound(message=msg)
        if not blob['external']:
            msg = _("Blob %s is not external") % blob_name
            raise exception.Forbidden(message=msg)

        modified_af = self._save_blob_info(
            context, af, field_name, blob_key, None)

        Notifier.notify(context, action_name, modified_af)
        return modified_af.to_dict()
