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
revision = '004'
down_revision = '003'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'glare_quotas',
        sa.Column('id', sa.String(255), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(255), nullable=False),
        sa.Column('quota_name', sa.String(32), nullable=False),
        sa.Column('quota_value', sa.String(255), nullable=False),
        sa.Column('type_name', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )


def downgrade():
    op.drop_table('glare_quotas')
