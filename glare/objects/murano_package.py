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

from oslo_versionedobjects import fields

from glare.objects import base
from glare.objects.meta import attribute
from glare.objects.meta import fields as glare_fields


Field = attribute.Attribute.init
Blob = attribute.BlobAttribute.init
List = attribute.ListAttribute.init


class MuranoPackage(base.BaseArtifact):

    fields = {
        'package': Blob(required_on_activate=False,
                        description="Murano Package binary."),
        'package_name': Field(fields.StringField,
                              description="Murano Package name."),
        'dependencies': List(glare_fields.Dependency,
                             required_on_activate=False,
                             description="List of package dependencies for "
                                         "this package."),
    }

    @classmethod
    def get_type_name(cls):
        return "murano_packages"
