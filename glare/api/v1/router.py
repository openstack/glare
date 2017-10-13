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

import importlib
import pkgutil
import sys

from oslo_config import cfg
from oslo_config import types as conf_types
from oslo_log import log as logging

from glare.api.v1 import resource
from glare.common import exception
from glare.common import wsgi
from glare.i18n import _

LOG = logging.getLogger(__name__)

external_api_opts = [
    cfg.ListOpt('custom_external_api_modules', default=[],
                item_type=conf_types.String(),
                help=_("List of custom user modules with external APIs that "
                       "will be attached to Glare dynamically during service "
                       "startup."))
]

CONF = cfg.CONF
CONF.register_opts(external_api_opts)


def import_submodules(module):
    """Import all submodules of a module.

    :param module: Package name
    :return: list of imported modules
    """
    package = sys.modules[module]
    return [
        importlib.import_module(module + '.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)]


class API(wsgi.Router):
    """WSGI router for Glare v1 API requests.

    API Router redirects incoming requests to appropriate WSGI resource method.
    """

    def __init__(self, mapper):

        glare_resource = resource.create_resource()
        reject_method_resource = wsgi.Resource(wsgi.RejectMethodController())

        # ---schemas---
        mapper.connect('/schemas',
                       controller=glare_resource,
                       action='list_type_schemas',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/schemas',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET')

        mapper.connect('/schemas/{type_name}',
                       controller=glare_resource,
                       action='show_type_schema',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/schemas/{type_name}',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET')

        # ---artifacts---
        mapper.connect('/artifacts/{type_name}',
                       controller=glare_resource,
                       action='list',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/artifacts/{type_name}',
                       controller=glare_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/artifacts/{type_name}',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET, POST')

        mapper.connect('/artifacts/{type_name}/{artifact_id}',
                       controller=glare_resource,
                       action='update',
                       conditions={'method': ['PATCH']})
        mapper.connect('/artifacts/{type_name}/{artifact_id}',
                       controller=glare_resource,
                       action='show',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/artifacts/{type_name}/{artifact_id}',
                       controller=glare_resource,
                       action='delete',
                       conditions={'method': ['DELETE']},
                       body_reject=True)
        mapper.connect('/artifacts/{type_name}/{artifact_id}',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET, PATCH, DELETE')

        # ---blobs---
        mapper.connect('/artifacts/{type_name}/{artifact_id}/{blob_path:.*?}',
                       controller=glare_resource,
                       action='download_blob',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/artifacts/{type_name}/{artifact_id}/{blob_path:.*?}',
                       controller=glare_resource,
                       action='upload_blob',
                       conditions={'method': ['PUT']})
        mapper.connect('/artifacts/{type_name}/{artifact_id}/{blob_path:.*?}',
                       controller=glare_resource,
                       action='delete_external_blob',
                       conditions={'method': ['DELETE']})
        mapper.connect('/artifacts/{type_name}/{artifact_id}/{blob_path:.*?}',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET, PUT, DELETE')

        # ---quotas---
        mapper.connect('/quotas',
                       controller=glare_resource,
                       action='set_quotas',
                       conditions={'method': ['PUT']})
        mapper.connect('/quotas',
                       controller=glare_resource,
                       action='list_all_quotas',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/quotas',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='PUT, GET')

        mapper.connect('/project-quotas',
                       controller=glare_resource,
                       action='list_project_quotas',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/project-quotas',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET')
        mapper.connect('/project-quotas/{project_id}',
                       controller=glare_resource,
                       action='list_project_quotas',
                       conditions={'method': ['GET']},
                       body_reject=True)
        mapper.connect('/project-quotas/{project_id}',
                       controller=reject_method_resource,
                       action='reject',
                       allowed_methods='GET')

        # Now register external APIs
        custom_module_list = []
        for module_name in CONF.custom_external_api_modules:
            try:
                custom_module_list.append(importlib.import_module(module_name))
            except Exception as e:
                LOG.exception(e)
                msg = ("Cannot import custom external API from module "
                       "%(module_name)%s. Error: %(error)s",
                       {'module_name': module_name, 'error': str(e)})
                raise exception.GlareException(msg)

        for module in custom_module_list:
            try:
                mapper.extend(module.mapper)
            except Exception as e:
                LOG.exception(e)
                msg = ("Cannot attach custom external API from module "
                       "%(module_name)%s. Error: %(error)s",
                       {'module_name': str(module), 'error': str(e)})
                raise exception.IncorrectExternalAPI(msg)

        super(API, self).__init__(mapper)
