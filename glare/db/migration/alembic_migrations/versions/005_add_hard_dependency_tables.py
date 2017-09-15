# Copyright 2017 OpenStack Foundation.
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

"""Add quota tables

Revision ID: 004
Revises: 003
Create Date: 2017-07-29 14:32:33.717353

"""

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'

import sqlalchemy as sa
from alembic import op

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'glare_dependencies',
        sa.Column('artifact_origin', sa.String(36), primary_key=True),
        sa.Column('artifact_source', sa.String(36), primary_key=True),
        sa.Column('artifact_dest', sa.String(36), primary_key=True),
        sa.PrimaryKeyConstraint('artifact_origin', 'artifact_source',
                                "artifact_dest"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_artifact_dependencies_origin_id',
                    'glare_dependencies',
                    ['artifact_origin']
                    )
    op.create_index('ix_artifact_dependencies_source_id',
                    'glare_dependencies',
                    ['artifact_source']
                    )
    op.create_index('ix_artifact_dependencies_dest_id',
                    'glare_dependencies',
                    ['artifact_dest']
                    )


def downgrade():
    op.drop_table('glare_dependencies')
