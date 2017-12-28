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

import datetime

from taskflow import states

from glare.db.sqlalchemy import api as db_api


def create_flow(context, flow_id, blob_url):
    return db_api.create_flow(
        flow_id=flow_id,
        blob_url=blob_url,
        status=states.PENDING,
        owner=context.tenant,
        expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
        session=db_api.get_session()
    )


def update_flow(flow_id, status=None, info=None):
    return db_api.update_flow(
        flow_id=flow_id,
        session=db_api.get_session(),
        status=status,
        info=info
    )


def get_flow(context, flow_id):
    return db_api.get_flow(
        context=context,
        flow_id=flow_id,
        session=db_api.get_session()
    )


def delete_flow(context, flow_id):
    return db_api.get_flow(
        context=context,
        flow_id=flow_id,
        session=db_api.get_session()
    )
