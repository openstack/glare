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

"""
Tests for database migrations.
For the opportunistic testing you need to set up a db named 'openstack_citest'
with user 'openstack_citest' and password 'openstack_citest' on localhost.
The test will then use that db and u/p combo to run the tests.
For postgres on Ubuntu this can be done with the following commands:
sudo -u postgres psql
postgres=# create user openstack_citest with createdb login password
      'openstack_citest';
postgres=# create database openstack_citest with owner openstack_citest;
"""

from oslo_db.sqlalchemy import test_base
from oslo_db.sqlalchemy import utils as db_utils
import sqlalchemy

from glare.tests.unit.db.migrations import test_migrations_base as base


class GlareMigrationsCheckers(object):

    snake_walk = False
    downgrade = False

    def assert_table(self, engine, table_name, indices, columns):
        table = db_utils.get_table(engine, table_name)
        index_data = [(index.name, index.columns.keys()) for index in
                      table.indexes]
        column_data = [column.name for column in table.columns]
        self.assertItemsEqual(columns, column_data)
        self.assertItemsEqual(indices, index_data)

    def test_walk_versions(self):
        self.walk_versions(self.engine, self.snake_walk, self.downgrade)

    def _pre_upgrade_001(self, engine):
        self.assertRaises(sqlalchemy.exc.NoSuchTableError,
                          db_utils.get_table, engine,
                          'glare_artifacts')
        self.assertRaises(sqlalchemy.exc.NoSuchTableError,
                          db_utils.get_table, engine,
                          'glare_artifact_tags')
        self.assertRaises(sqlalchemy.exc.NoSuchTableError,
                          db_utils.get_table, engine,
                          'glare_artifact_properties')
        self.assertRaises(sqlalchemy.exc.NoSuchTableError,
                          db_utils.get_table, engine,
                          'glare_artifact_blobs')

    def _check_001(self, engine, data):
        artifacts_indices = [('ix_glare_artifact_name_and_version',
                              ['name', 'version_prefix', 'version_suffix']),
                             ('ix_glare_artifact_type',
                              ['type_name']),
                             ('ix_glare_artifact_status', ['status']),
                             ('ix_glare_artifact_visibility', ['visibility']),
                             ('ix_glare_artifact_owner', ['owner'])]
        artifacts_columns = ['id',
                             'name',
                             'type_name',
                             'version_prefix',
                             'version_suffix',
                             'version_meta',
                             'description',
                             'visibility',
                             'status',
                             'owner',
                             'created_at',
                             'updated_at',
                             'activated_at']
        self.assert_table(engine, 'glare_artifacts', artifacts_indices,
                          artifacts_columns)

        tags_indices = [('ix_glare_artifact_tags_artifact_id',
                         ['artifact_id']),
                        ('ix_glare_artifact_tags_artifact_id_tag_value',
                         ['artifact_id',
                          'value'])]
        tags_columns = ['id',
                        'artifact_id',
                        'value']
        self.assert_table(engine, 'glare_artifact_tags', tags_indices,
                          tags_columns)

        prop_indices = [
            ('ix_glare_artifact_properties_artifact_id',
             ['artifact_id']),
            ('ix_glare_artifact_properties_name', ['name'])]
        prop_columns = ['id',
                        'artifact_id',
                        'name',
                        'string_value',
                        'int_value',
                        'numeric_value',
                        'bool_value',
                        'key_name',
                        'position']
        self.assert_table(engine, 'glare_artifact_properties', prop_indices,
                          prop_columns)

        blobs_indices = [
            ('ix_glare_artifact_blobs_artifact_id', ['artifact_id']),
            ('ix_glare_artifact_blobs_name', ['name'])]
        blobs_columns = ['id',
                         'artifact_id',
                         'size',
                         'checksum',
                         'name',
                         'key_name',
                         'external',
                         'status',
                         'content_type',
                         'url']
        self.assert_table(engine, 'glare_artifact_blobs', blobs_indices,
                          blobs_columns)

        locks_indices = []
        locks_columns = ['id']
        self.assert_table(engine, 'glare_artifact_locks', locks_indices,
                          locks_columns)


class TestMigrationsMySQL(GlareMigrationsCheckers,
                          base.BaseWalkMigrationTestCase,
                          test_base.MySQLOpportunisticTestCase):
    pass


class TestMigrationsPostgresql(GlareMigrationsCheckers,
                               base.BaseWalkMigrationTestCase,
                               test_base.PostgreSQLOpportunisticTestCase):
    pass
