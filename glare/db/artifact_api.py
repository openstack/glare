# Copyright (c) 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Database API for all artifact types"""

from oslo_db import exception as db_exception
from oslo_log import log as logging
from retrying import retry
import six

from glare.db.sqlalchemy import api
from glare.i18n import _LW
from glare import locking

LOG = logging.getLogger(__name__)


def _retry_on_connection_error(exc):
    """Function to retry a DB API call if connection error was received."""

    if isinstance(exc, db_exception.DBConnectionError):
        LOG.warning(_LW("Connection error detected. Retrying..."))
        return True
    return False


class ArtifactAPI(object):

    def _serialize_values(self, values):
        new_values = {}
        if 'tags' in values:
            new_values['tags'] = values.pop('tags') if values['tags'] else []
        for key, value in six.iteritems(values):
            if key in api.BASE_ARTIFACT_PROPERTIES:
                new_values[key] = value
            else:
                new_values.setdefault('properties', {})[key] = value
        return new_values

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def create(self, context, values, type):
        """Create new artifact in db and return dict of values to the user

        :param context: user context
        :param values: dict of values that needs to be saved to db
        :param type: string indicates artifact of what type to create
        :return: dict of created values
        """
        values = self._serialize_values(values)
        values['type_name'] = type
        session = api.get_session()
        return api.create(context, values, session)

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def update(self, context, artifact_id, values):
        """Update artifact values in database

        :param artifact_id: id of artifact that needs to be updated
        :param context: user context
        :param values: values that needs to be updated
        :return: dict of updated artifact values
        """
        session = api.get_session()
        return api.update(context, artifact_id,
                          self._serialize_values(values), session)

    def update_blob(self, context, artifact_id, values):
        """Create and update blob records in db

        :param artifact_id: id of artifact that needs to be updated
        :param context: user context
        :param values: blob values that needs to be updated
        :return: dict of updated artifact values
        """
        session = api.get_session()
        return api.update(context, artifact_id,
                          {'blobs': values}, session)

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def delete(self, context, artifact_id):
        """Delete artifacts from db

        :param context: user context
        :param artifact_id: id of artifact that needs to be deleted
        """
        session = api.get_session()
        api.delete(context, artifact_id, session)

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def get(self, context, artifact_id):
        """Return artifact values from database

        :param context: user context
        :param artifact_id: id of the artifact
        :return: dict of artifact values
        """
        session = api.get_session()
        return api.get(context, artifact_id, session)

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def list(self, context, filters, marker, limit, sort, latest):
        """List artifacts from db

        :param context: user request context
        :param filters: filter conditions from url
        :param marker: id of first artifact where we need to start
        artifact lookup
        :param limit: max number of items in list
        :param sort: sort conditions
        :param latest: flag that indicates, that only artifacts with highest
        versions should be returned in output
        :return: list of artifacts. Each artifact is represented as dict of
        values.
        """
        session = api.get_session()
        return api.get_all(context=context, session=session, filters=filters,
                           marker=marker, limit=limit, sort=sort,
                           latest=latest)


class ArtifactLockApi(locking.LockApiBase):
    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def create_lock(self, context, lock_key):
        session = api.get_session()
        return api.create_lock(context, lock_key, session)

    @retry(retry_on_exception=_retry_on_connection_error, wait_fixed=1000,
           stop_max_attempt_number=20)
    def delete_lock(self, context, lock_id):
        session = api.get_session()
        api.delete_lock(context, lock_id, session)
