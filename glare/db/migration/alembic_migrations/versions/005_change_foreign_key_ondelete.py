# Copyright 2018 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Change foreign key ondelete

Revision ID: 005
Revises: 004
Create Date: 2018-01-25 15:41:22.421484

"""

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'

from alembic import op

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'

glare_tables = [
    'glare_artifact_tags',
    'glare_artifact_blobs',
    'glare_artifact_properties'
]


def upgrade():
    dialect = op.get_bind().engine.name
    # Alembic has no support for ALTER of constraints in SQLite dialect
    if dialect == 'sqlite':
        return

    for glare_table in glare_tables:
        op.drop_constraint(
            "glare_artifacts.id", glare_table, type_="foreignkey")
        op.create_foreign_key(
            "glare_artifacts.id", glare_table, "glare_artifacts",
            ["artifact_id"], ["id"], ondelete="CASCADE")


def downgrade():
    dialect = op.get_bind().engine.name
    # Alembic has no support for ALTER of constraints in SQLite dialect
    if dialect == 'sqlite':
        return

    for glare_table in glare_tables:
        op.drop_constraint(
            "glare_artifacts.id", glare_table, type_="foreignkey")
        op.create_foreign_key(
            "glare_artifacts.id", glare_table, "glare_artifacts",
            ["artifact_id"], ["id"])
