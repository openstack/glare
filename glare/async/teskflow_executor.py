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

from oslo_log import log as logging
from oslo_utils import uuidutils
from taskflow import engines
from taskflow.patterns import linear_flow as lf
from taskflow import task


from glare.async import flow
from glare.async import flow_listener
from glare.common import exception as exc
from glare.common import utils

LOG = logging.getLogger(__name__)


class FlowExecutor(object):

    def __init__(self, context, af, field_name, fd, blob_key, blob_data):
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
        self.blob_data = blob_data
        self.flow_id = uuidutils.generate_uuid()
        try:
            self.fd, self.path = utils.create_temporary_file(fd)
        except exc.GlareException:
            raise
        except Exception as e:
            raise exc.BadRequest(message=str(e))
        self.blob_data['status'] = 'staged'
        self._save_blob_info(self.blob_data)

    def _save_blob_info(self, value):
        """Save blob instance in database."""
        if self.blob_key is not None:
            # Insert blob value in the folder
            folder = getattr(self.af, self.field_name)
            if value is not None:
                folder[self.blob_key] = value
            else:
                del folder[self.blob_key]
            value = folder
        return self.af.update_blob(
            self.context, self.af.id, self.field_name, value)

    def _generate_flow(self):
        flow = lf.Flow(self.flow_id)
        flow.add(CallUploadHook(
            "CallUploadHook",
            inject={
                'context': self.context,
                'af': self.af,
                'field_name': self.field_name,
                'fd': self.fd,
                'blob_key': self.blob_key
            }
        ))
        return flow

    def run(self):
        flow.create_flow(self.context, self.flow_id, self.blob_url)
        engine = engines.load(
            flow=self._generate_flow(), engine='parallel', executor='threaded',
            max_workers=1)
        with flow_listener.DynamicLoggingListener(engine, self.flow_id,
                                                  log=LOG):
            engine.run()


class CallUploadHook(task.Task):
    def __init__(self, name, inject=None):
        super(CallUploadHook, self).__init__(name, inject=inject)

    def execute(self, context, af, field_name, fd, blob_key):
        return af.validate_upload(context, af, field_name, fd, blob_key)


class ActivateBlob(task.Task):
    def __init__(self, name, inject=None):
        super(ActivateBlob, self).__init__(name, inject=inject)

    def execute(self, context, af, field_name, fd, blob_key):
        return af.validate_upload(context, af, field_name, fd, blob_key)
