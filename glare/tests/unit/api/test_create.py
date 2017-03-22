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


from glare.api.v1 import resource
from glare.common import exception as exc
from glare.tests.unit.api import base


class TestArtifactAPI(base.BaseTestArtifactAPI):

    """Test Glare API Controller."""

    def test_create_artifact_minimal(self):
        req = self.get_fake_request(user=self.users['user1'])
        values = {'name': 'ttt'}

        res = self.controller.create(req, 'sample_artifact', values)
        self.assertEqual('ttt', res['name'])
        self.assertEqual('0.0.0', res['version'])
        self.assertEqual(self.users['user1']['tenant_id'], res['owner'])
        self.assertEqual('drafted', res['status'])
        self.assertEqual('private', res['visibility'])
        self.assertEqual('', res['description'])
        self.assertEqual({}, res['metadata'])
        self.assertEqual([], res['tags'])

    def test_create_artifact_with_fields(self):
        req = self.get_fake_request(user=self.users['user1'])
        values = {'name': 'ttt', 'version': '1.0',
                  'description': "Test Artifact", 'tags': ['test'],
                  'metadata': {'type': 'image'}}

        res = self.controller.create(req, 'sample_artifact', values)
        self.assertEqual('ttt', res['name'])
        self.assertEqual('1.0.0', res['version'])
        self.assertEqual(self.users['user1']['tenant_id'], res['owner'])
        self.assertEqual('drafted', res['status'])
        self.assertEqual('private', res['visibility'])
        self.assertEqual('Test Artifact', res['description'])
        self.assertEqual({'type': 'image'}, res['metadata'])
        self.assertEqual(['test'], res['tags'])

    def test_create_artifact_no_name(self):
        req = self.get_fake_request(user=self.users['user1'])
        values = {'version': '1.0'}
        self.assertRaises(exc.BadRequest, self.controller.create,
                          req, 'sample_artifact', values)

    def test_create_artifact_not_existing_field(self):
        req = self.get_fake_request(user=self.users['user1'])
        values = {'name': 'test', 'not_exist': 'some_value'}
        self.assertRaises(exc.BadRequest, self.controller.create,
                          req, 'sample_artifact', values)

    def test_create_artifact_blob_upload(self):
        req = self.get_fake_request(user=self.users['user1'])
        values = {'name': 'test', 'blob': 'DATA'}
        self.assertRaises(exc.BadRequest, self.controller.create,
                          req, 'sample_artifact', values)

    def test_list_artifacts(self):
        req = self.get_fake_request(user=self.users['user1'])
        res = resource.ArtifactsController().list(req, 'images', [])
        self.assertEqual({'artifacts': [], 'type_name': 'images'}, res)
