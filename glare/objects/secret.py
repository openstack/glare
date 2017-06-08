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

# Import fields from oslo.vo
from oslo_versionedobjects import fields

# Import glare addons:
# The parent class for all artifacts inherited from
# oslo_versionedobjects.base.VersionedObject
from glare.objects import base as base_artifact
# Glare wrapper for oslo_versionedobjects.fields
from glare.objects.meta import validators
# Additional Glare field types, like Blob or Link
from glare.objects.meta import wrappers

Field = wrappers.Field.init
Blob = wrappers.BlobField.init
Dict = wrappers.DictField.init
Folder = wrappers.FolderField.init


class Secret(base_artifact.BaseArtifact):
    """The purpose this glare artifact, Secret, is to enable the user to store
    'secret' data such as: Private key, Certificate, Password, SSH keys Etc.
    The secret data will be encrypted and then will
    be saved in 'payload' artifact's field.
    *payload_content_encoding field represents the encryption method that had
     been used for saving 'payload'
    """
    VERSION = '1.0'

    @classmethod
    def get_type_name(cls):
        return "secret"

    fields = {
        'payload': Field(  # The encrypted secret data
            fields.StringField,
            required_on_activate=True,
            filter_ops=(wrappers.FILTER_EQ,),
            validators=[
                validators.AllowedValues(validators.MinStrLen(1))],
            nullable=False,
            description="The secret's data to be stored"
        ),

        'payload_content_type': Field(  # E.G. application/octet-stream
            fields.StringField,
            required_on_activate=False,
            default=None,
            filter_ops=(wrappers.FILTER_EQ,),
            description="The media type for the content of the payload."
                        "The content-types that can be used to retrieve"
                        "the payload.",
        ),

        'payload_content_encoding': Field(
            fields.StringField,
            required_on_activate=False,
            default=None,
            filter_ops=(wrappers.FILTER_EQ,),
            validators=[validators.AllowedValues(["base64"])],
            description="Required if payload is encoded."
                        "The encoding used for the payload to be"
                        " able to include it in the JSON request "
                        "(only base64 supported)"
        ),

        'secret_type': Field(
            fields.StringField,
            required_on_activate=False,
            default="opaque",
            filter_ops=(wrappers.FILTER_EQ,),
            validators=[validators.AllowedValues([
                "symmetric, public ,private,"
                " passphrase, certificate, opaque"])],
            description="Used to indicate the type of secret being stored",
        ),

        'algorithm': Field(
            fields.StringField,
            required_on_activate=False,
            filter_ops=(wrappers.FILTER_EQ,),
            default=None,
            description="Metadata provided by a user or system for"
                        " informational purposes",
        ),

        'bit_length': Field(
            fields.IntegerField,
            required_on_activate=False,
            filter_ops=wrappers.FILTERS,
            sortable=True,
            validators=[validators.MinNumberSize(1)],
            description=" Metadata provided by a user or system"
                        " for informational purposes."
                        " Value must be greater than zero."
        ),

        'mode': Field(
            fields.StringField,
            required_on_activate=False,
            filter_ops=(wrappers.FILTER_EQ,),
            default=None,
            description="Metadata provided by a user or"
                        " system for informational purposes."),
    }
