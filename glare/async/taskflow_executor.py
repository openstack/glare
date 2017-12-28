# Copyright 2017 - Nokia Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os

from oslo_log import log as logging
from oslo_utils import uuidutils
from taskflow import engines
from taskflow.patterns import linear_flow as lf
from taskflow import task


from glare.async import flow as flow_api
from glare.async import flow_listener
from glare.common import exception as exc
from glare.common import store_api
from glare.common import utils

LOG = logging.getLogger(__name__)


class FlowExecutor(object):

    def __init__(self, context, af, field_name, blob_key, fd, blob_info,
                 blob_id, default_store):
        blob_url = '/artifacts/%(name)s/%(id)s/%(field_name)s' % {
            "name": af.get_type_name(),
            "id": af.id,
            "field_name": field_name
        }
        if blob_key is not None:
            blob_url += '/%s' % blob_key

        self.context = context
        self.blob_url = blob_url
        self.af = af
        self.field_name = field_name
        self.blob_key = blob_key
        self.blob_info = blob_info
        self.blob_id = blob_id
        self.flow_id = uuidutils.generate_uuid()
        self.default_store = default_store
        try:
            self.fd, self.path = utils.create_temporary_file(fd)
        except exc.GlareException:
            raise
        except Exception as e:
            raise exc.BadRequest(message=str(e))
        self.fd.seek(0)
        self.blob_info['status'] = 'staged'
        self._save_blob_info(self.context, self.af, self.field_name,
                             self.blob_key, self.blob_info)

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

    def _activate_blob(self, context, af, field_name, blob_key, blob_info,
                       location_uri, size, checksums):
        # update blob info and activate it
        blob_info.update({'url': location_uri,
                          'status': 'active',
                          'size': size})
        blob_info.update(checksums)
        self._save_blob_info(context, af, field_name, blob_key, blob_info)

    def _save_blob_to_store(self, blob_id, fd, context):
        return store_api.save_blob_to_store(blob_id=blob_id,
                                            blob=fd,
                                            context=context,
                                            max_size=self.blob_info['size'],
                                            store_type=self.default_store)

    def _generate_flow(self):
        flow = lf.Flow(self.flow_id)
        flow.add(task.FunctorTask(self.af.pre_upload_hook, provides='fd'))
        flow.add(task.FunctorTask(
            self._save_blob_to_store,
            provides=('location_uri', 'size', 'checksums')))
        flow.add(task.FunctorTask(self._activate_blob))
        flow.add(task.FunctorTask(self._remove_temp_file,
                                  inject={'path': self.path}))

        return flow

    def _remove_temp_file(self, path):
        os.remove(path)

    def run(self):
        flow_api.create_flow(self.context, self.flow_id, self.blob_url)
        engine = engines.load(
            flow=self._generate_flow(), engine='parallel', executor='threaded',
            max_workers=1, store={
                'context': self.context,
                'af': self.af,
                'field_name': self.field_name,
                'fd': self.fd,
                'blob_key': self.blob_key,
                'blob_info': self.blob_info,
                'blob_id': self.blob_id,
                'store_type': self.default_store,
                'max_size': self.blob_info['size']
            })
        with flow_listener.DynamicLoggingListener(
                engine, self.flow_id, log=LOG):
            engine.run()
