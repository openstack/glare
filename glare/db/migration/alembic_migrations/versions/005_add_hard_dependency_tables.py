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

from alembic import op
import sqlalchemy as sa

"""Add glare_hard_dependencies tables

Revision ID: 005
Revises: 004
Create Date: 2017-11-29 14:32:33.717353

"""

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'glare_hard_dependencies',
        sa.Column('artifact_origin', sa.String(36),
                  sa.ForeignKey('glare_artifacts.id'), primary_key=True),
        sa.Column('artifact_source', sa.String(36),
                  sa.ForeignKey('glare_artifacts.id'), primary_key=True),
        sa.Column('artifact_target', sa.String(36),
                  sa.ForeignKey('glare_artifacts.id'), primary_key=True),
        sa.PrimaryKeyConstraint('artifact_origin', 'artifact_source',
                                "artifact_target"),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_artifact_dependencies_origin_id',
                    'glare_hard_dependencies',
                    ['artifact_origin']
                    )
    op.create_index('ix_artifact_dependencies_source_id',
                    'glare_hard_dependencies',
                    ['artifact_source']
                    )
    op.create_index('ix_artifact_dependencies_target_id',
                    'glare_hard_dependencies',
                    ['artifact_target']
                    )


def downgrade():
    op.drop_table('glare_hard_dependencies')
