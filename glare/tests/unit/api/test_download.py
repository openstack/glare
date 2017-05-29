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

from six import BytesIO

from glare.common import exception as exc
from glare.db import artifact_api
from glare.tests.unit import base


class TestArtifactDownload(base.BaseTestArtifactAPI):
    def setUp(self):
        super(TestArtifactDownload, self).setUp()
        values = {'name': 'ttt', 'version': '1.0'}
        self.sample_artifact = self.controller.create(
            self.req, 'sample_artifact', values)

        self.controller.upload_blob(
            self.req, 'sample_artifact', self.sample_artifact['id'], 'blob',
            BytesIO(b'aaa'), 'application/octet-stream')

        artifact = self.controller.show(self.req, 'sample_artifact',
                                        self.sample_artifact['id'])
        self.assertEqual(3, artifact['blob']['size'])
        self.assertEqual('active', artifact['blob']['status'])

    def test_download_basic(self):
        downloaded_blob = self.controller.download_blob(
            self.req, 'sample_artifact',
            self.sample_artifact['id'], 'blob')
        self.assertEqual('aaa', downloaded_blob['data'].data)

    def test_download_from_folders(self):
        self.controller.upload_blob(
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'dict_of_blobs/folder1',
            BytesIO(b'bbb'), 'application/octet-stream')
        downloaded_blob = self.controller.download_blob(
            self.req, 'sample_artifact',
            self.sample_artifact['id'], 'dict_of_blobs/folder1')
        self.assertEqual('bbb', downloaded_blob['data'].data)

    def test_download_from_non_existing_fields(self):
        self.assertRaises(exc.BadRequest, self.controller.download_blob,
                          self.req, 'sample_artifact',
                          self.sample_artifact['id'], "NON_EXISTING_FIELD")

    def test_download_of_saving_blob(self):
        self.sample_artifact = self.controller.show(
            self.req, 'sample_artifact', self.sample_artifact['id'])

        # Change status of the blob to 'saving'
        self.sample_artifact['blob']['status'] = 'saving'
        artifact_api.ArtifactAPI().update_blob(
            self.req.context, self.sample_artifact['id'],
            {'blob': self.sample_artifact['blob']})

        self.sample_artifact = self.controller.show(
            self.req, 'sample_artifact', self.sample_artifact['id'])
        self.assertEqual('saving', self.sample_artifact['blob']['status'])

        # assert that we can't download while blob in saving status
        self.assertRaises(exc.BadRequest, self.controller.download_blob,
                          self.req, 'sample_artifact',
                          self.sample_artifact['id'], "blob")
