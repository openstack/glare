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

from glare.api.middleware import context
from glare.common import exception as exc
from glare import engine
from glare.tests.unit import base


class TestScopedLocks(base.BaseTestCase):
    """Test class for scoped locks."""

    def setUp(self):
        super(TestScopedLocks, self).setUp()
        self.engine = engine.Engine()
        kwargs = {
            'user': 'user1',
            'tenant': 'user1',
            'roles': '',
            'is_admin': False
        }
        self.context = context.RequestContext(**kwargs)

    def test_create_lock_basic(self):
        # create private scoped lock
        lock = self.engine._create_scoped_lock(
            self.context, 'sample_artifact', 'my_art', '1.0.0', 'user1')
        self.assertEqual('sample_artifact:my_art:1.0.0:user1', lock.lock_key)

        # create another lock for this scope fails with Conflict error
        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '1.0.0', 'user1')

        # create public scoped lock
        lock = self.engine._create_scoped_lock(
            self.context, 'sample_artifact', 'my_art', '1.0.0', 'user1',
            visibility='public')
        self.assertEqual('sample_artifact:my_art:1.0.0', lock.lock_key)

        # create another lock for this scope fails with Conflict error
        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '1.0.0', 'user1',
            visibility='public')

    def test_scoped_lock_bad_values(self):
        # too long name
        self.assertRaises(
            exc.BadRequest, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'a' * 1000, '2.0.0', 'user1')

        # no name
        self.assertRaises(
            exc.BadRequest, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', '', '2.0.0', 'user1')

        # no version
        self.assertRaises(
            exc.BadRequest, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', '', '2.0.0', 'user1')

        # invalid version
        self.assertRaises(
            exc.BadRequest, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '', 'user1')

        # invalid visibility
        self.assertRaises(
            exc.BadRequest, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '2.0.0', 'user1',
            visibility='INVALID')

    def test_scoped_lock_version_coercion(self):
        # versions 3, 3.0 and 3.0.0 are the same
        lock = self.engine._create_scoped_lock(
            self.context, 'sample_artifact', 'my_art', '3', 'user1')
        self.assertEqual('sample_artifact:my_art:3.0.0:user1', lock.lock_key)

        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '3.0', 'user1')

        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '3.0.0', 'user1')

        # versions 3-beta, 3.0-beta, 3.0.0-beta are the same
        lock = self.engine._create_scoped_lock(
            self.context, 'sample_artifact', 'my_art', '3-beta', 'user1')
        self.assertEqual('sample_artifact:my_art:3.0.0-beta:user1',
                         lock.lock_key)

        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '3.0-beta', 'user1')

        self.assertRaises(
            exc.Conflict, self.engine._create_scoped_lock,
            self.context, 'sample_artifact', 'my_art', '3.0.0-beta', 'user1')
