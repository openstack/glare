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

from glare.db.sqlalchemy import api


def get_hard_dependencies(artifact_id):
    session = api.get_session()
    return api.get_hard_dependencies(artifact_id, session)


def get_hard_dependencies_children(artifact_id):
    session = api.get_session()
    return api.get_hard_dependencies_children(artifact_id, session)


def set_hard_dependencies(source_id, target_id):
    session = api.get_session()
    api.set_hard_dependencies(source_id, target_id, session)


def delete_hard_dependencies(source_id, target_id):
    session = api.get_session()
    api.delete_hard_dependencies(source_id, target_id,  session)


def delete_hard_dependencies_for_art_deletion(art_to_be_deleted_id):
    session = api.get_session()
    api.delete_hard_dependencies_for_art_deletion(art_to_be_deleted_id,
                                                  session)
