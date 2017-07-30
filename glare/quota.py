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

from oslo_config import cfg

from glare.common import exception
from glare.db.sqlalchemy import api
from glare.i18n import _

CONF = cfg.CONF


def verify_artifact_count(context, type_name):
    global_limit = CONF.max_artifact_number
    type_limit = getattr(
        CONF, 'artifact_type:' + type_name).max_artifact_number

    # update limits if they were reassigned for project
    project_id = context.tenant
    quotas = get_project_quotas(project_id)
    for q in quotas:
        if q['quota_name'] == 'max_artifact_number':
            if q['type_name'] is None:
                global_limit = q['quota_value']
            elif q['type_name'] == type_name:
                type_limit = q['quota_value']

    session = api.get_session()
    # the whole amount of created artifacts
    whole_number = api.count_artifact_number(context, session)

    if whole_number >= global_limit:
        msg = _("Can't create artifact because of global quota "
                "limit is %(global_limit)d artifacts. "
                "You have %(whole_number)d artifact(s).") % {
            'global_limit': global_limit, 'whole_number': whole_number}
        raise exception.Forbidden(msg)

    if type_limit is not None:
        # the amount of artifacts for specific type
        type_number = api.count_artifact_number(
            context, session, type_name)

        if type_number >= type_limit:
            msg = _("Can't create artifact because of quota limit for "
                    "artifact type '%(type_name)s' is %(type_limit)d "
                    "artifacts. You have %(type_number)d artifact(s) "
                    "of this type.") % {
                'type_name': type_name,
                'type_limit': type_limit,
                'type_number': type_number}
            raise exception.Forbidden(msg)


def verify_uploaded_data_amount(context, type_name, data_amount):
    global_limit = CONF.max_uploaded_data
    type_limit = getattr(CONF, 'artifact_type:' + type_name).max_uploaded_data

    # update limits if they were reassigned for project
    project_id = context.tenant
    quotas = get_project_quotas(project_id)
    for q in quotas:
        if q['quota_name'] == 'max_uploaded_data':
            if q['type_name'] is None:
                global_limit = q['quota_value']
            elif q['type_name'] == type_name:
                type_limit = q['quota_value']

    session = api.get_session()
    # the whole amount of created artifacts
    whole_number = api.calculate_uploaded_data(context, session)

    if whole_number + data_amount > global_limit:
        msg = _("Can't upload %(data_amount)d byte(s) because of global quota "
                "limit: %(global_limit)d. "
                "You have %(whole_number)d bytes uploaded.") % {
            'data_amount': data_amount,
            'global_limit': global_limit,
            'whole_number': whole_number}
        raise exception.Forbidden(msg)

    if type_limit is not None:
        # the amount of artifacts for specific type
        type_number = api.calculate_uploaded_data(
            context, session, type_name)

        if type_number + data_amount > type_limit:
            msg = _("Can't upload %(data_amount)d byte(s) because of quota "
                    "limit for artifact type '%(type_name)s': %(type_limit)d. "
                    "You have %(type_number)d bytes uploaded for this "
                    "type.") % {
                'data_amount': data_amount,
                'type_name': type_name,
                'type_limit': type_limit,
                'type_number': type_number}
            raise exception.Forbidden(msg)


def create_quota(project_id, name, value, type_name=None):
    session = api.get_session()
    return api.create_quota(project_id, name, value, session, type_name)


def update_quota(project_id, quota_id, value):
    session = api.get_session()
    return api.update_quota(project_id, quota_id, value, session)


def get_quota(project_id, quota_id):
    session = api.get_session()
    return api.get_quota(project_id, quota_id, session)


def delete_quota(project_id, quota_id):
    session = api.get_session()
    return api.delete_quota(project_id, quota_id, session)


def get_project_quotas(project_id):
    session = api.get_session()
    return api.get_all_project_quotas(project_id, session)
