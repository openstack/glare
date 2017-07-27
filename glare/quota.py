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
    global_limit = CONF.max_artifact_count
    type_limit = getattr(CONF, type_name).max_artifact_count

    session = api.get_session()
    # the whole amount of created artifacts
    whole_number = api.count_artifact_number(context, session)

    if whole_number + 1 >= global_limit:
        msg = _("Can't create artifact because of global quota "
                "limit: %(global_limit)d. "
                "You have %(whole_number)d artifact(s).") % {
            'global_limit': global_limit, 'whole_number': whole_number}
        raise exception.Forbidden(msg)

    if type_limit is not None:
        # the amount of artifacts for specific type
        type_number = api.count_artifact_number(
            context, session, type_name)

        if type_number + 1 >= type_limit:
            msg = _("Can't create artifact because of quota limit for "
                    "artifact type %(type_name)s: %(global_limit)d. "
                    "You have %(whole_number)d artifact(s) of this "
                    "type.") % {
                'type_name': type_name,
                'global_limit': global_limit,
                'whole_number': whole_number}
            raise exception.Forbidden(msg)


def verify_uploaded_data_amount(context, type_name, data_amount):
    global_limit = CONF.max_uploaded_data
    type_limit = getattr(CONF, type_name).max_uploaded_data

    session = api.get_session()
    # the whole amount of created artifacts
    whole_number = api.calculate_uploaded_data(context, session)

    if whole_number + data_amount >= global_limit:
        msg = _("Can't upload %(data_amount)d bytes because of global quota "
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

        if type_number + data_amount >= type_limit:
            msg = _("Can't upload %(data_amount)d bytes because of quota "
                    "limit for artifact type %(type_name)s: %(global_limit)d. "
                    "You have %(whole_number)d bytes uploaded for this "
                    "type.") % {
                'data_amount': data_amount,
                'type_name': type_name,
                'global_limit': global_limit,
                'whole_number': whole_number}
            raise exception.Forbidden(msg)