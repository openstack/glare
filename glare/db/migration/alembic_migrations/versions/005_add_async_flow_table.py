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

Revision ID: 005
Revises: 004
Create Date: 2017-08-16 01:07:45.277328

"""

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'

from alembic import op
import sqlalchemy as sa

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'


def upgrade():
    op.create_table(
        'glare_flows',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('blob_url', sa.String(2600), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('owner', sa.String(255), nullable=False),
        sa.Column('info', sa.Text()),
        mysql_engine=MYSQL_ENGINE,
        mysql_charset=MYSQL_CHARSET
    )

    op.create_index('ix_glare_flow_status',
                    'glare_flows',
                    ['status']
                    )
    op.create_index('ix_glare_flow_owner',
                    'glare_flows',
                    ['owner']
                    )
    op.create_index('ix_glare_flow_expires_at',
                    'glare_flows',
                    ['expires_at']
                    )


def downgrade():
    op.drop_table('glare_flows')
