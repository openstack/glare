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

from oslo_versionedobjects import fields

from glare.common import exception
from glare.objects import base
from glare.objects.meta import attribute


Field = attribute.Attribute.init
Blob = attribute.BlobAttribute.init
Dict = attribute.DictAttribute.init
BlobDict = attribute.BlobDictAttribute.init


class All(base.BaseArtifact):

    fields = {
        'type_name': Field(fields.StringField,
                           description="Name of artifact type."),
    }

    @classmethod
    def get_type_name(cls):
        return "all"

    @classmethod
    def create(cls, context, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def update(cls, context, af, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def get_action_for_updates(cls, context, artifact, updates, registry):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def delete(cls, context, af):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def activate(cls, context, af, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def reactivate(cls, context, af, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def deactivate(cls, context, af, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def publish(cls, context, af, values):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def upload_blob(cls, context, af, field_name, fd, content_type):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def download_blob(cls, context, af, field_name):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def upload_blob_dict(cls, context, af, field_name, blob_key, fd,
                         content_type):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def download_blob_dict(cls, context, af, field_name, blob_key):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def add_blob_location(cls, context, af, field_name, location, blob_meta):
        raise exception.BadRequest("This type is read only.")

    @classmethod
    def add_blob_dict_location(cls, context, af, field_name,
                               blob_key, location, blob_meta):
        raise exception.BadRequest("This type is read only.")
