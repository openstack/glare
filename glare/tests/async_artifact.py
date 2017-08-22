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

import time

from glare.objects import base as base_artifact
from glare.objects.meta import wrappers

Field = wrappers.Field.init
Dict = wrappers.DictField.init
List = wrappers.ListField.init
Blob = wrappers.BlobField.init
Folder = wrappers.FolderField.init


class AsyncArtifact(base_artifact.BaseArtifact):
    """Artifact type for testing asynchronous processing."""
    VERSION = '1.0'

    fields = {
        'blob': Blob(required_on_activate=False, mutable=True,
                     description="I am Blob", upload_workflow='async'),
    }

    @classmethod
    def get_type_name(cls):
        return "async_artifact"

    @classmethod
    def pre_upload_hook(cls, context, af, field_name, blob_key, fd):
        time.sleep(3)
        with open("/tmp/test.txt", "w") as f:
            f.write(str(fd.read()))
        fd.seek(0)
        return fd
