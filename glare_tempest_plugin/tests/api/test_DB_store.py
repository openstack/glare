# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import hashlib
import testtools


from glare_tempest_plugin.tests.api import base
from pprint import pformat
from tempest import config
from tempest.lib import exceptions as exc

CONF = config.CONF


class TestDownloadSanity(base.BaseArtifactTest):

    @testtools.testcase.attr('TestDownloadSanity')
    def test_blob_dict(self):
        # Getting empty artifact list
        response = self.artifacts_client.list_artifacts('sample_artifact')
        expected = {u'first': u'/artifacts/sample_artifact',
                    u'sample_artifact': [],
                    u'schema': u'/schemas/sample_artifact'}
        self.assertEqual(expected, response)

        # Create a test artifact
        art = self.artifacts_client.create_artifact('sample_artifact',
                                                    'sample_art1')
        self.assertIsNotNone(art['id'], pformat(art))

        # Get the artifact which should have a generated id and status
        # 'drafted'
        art_1 = self.artifacts_client.get_artifact(
            'sample_artifact', art['id'])
        self.assertIsNotNone(art_1['id'], pformat(art_1))
        self.assertEqual('drafted', art_1['status'])

        data = "data" * 100
        self.artifacts_client.upload_blob('sample_artifact', art['id'],
                                          '/dict_of_blobs/new_blob', data)

        # Download data from blob dict
        self.assertEqual(data,
                         self.artifacts_client.download_blob(
                             'sample_artifact', art_1['id'],
                             '/dict_of_blobs/new_blob'), pformat(art_1))

        # download blob from undefined dict property
        self.assertRaises(exc.BadRequest, self.artifacts_client.download_blob,
                          'sample_artifact', art_1['id'],
                          '/not_a_dict/not_a_blob')

    @testtools.testcase.attr('TestDownloadSanity')
    def test_blob_download(self):
        data = 'some_arbitrary_testing_data'
        art = self.artifacts_client.create_artifact('sample_artifact',
                                                    'test_af')

        # download not uploaded blob
        self.assertRaises(exc.BadRequest, self.artifacts_client.download_blob,
                          'sample_artifact', art['id'], 'blob')

        # download blob from not existing artifact
        self.assertRaises(exc.NotFound, self.artifacts_client.download_blob,
                          'not_exist_artifact', art['id'], 'blob')

        # download blob from undefined property
        self.assertRaises(exc.BadRequest, self.artifacts_client.download_blob,
                          'sample_artifact', art['id'], 'undefined_prop')

        # upload data
        art2 = self.artifacts_client.upload_blob('sample_artifact', art['id'],
                                                 'blob', data)

        self.assertEqual('active', art2['blob']['status'], pformat(art2))
        md5 = hashlib.md5(data.encode('UTF-8')).hexdigest()
        sha1 = hashlib.sha1(data.encode('UTF-8')).hexdigest()
        sha256 = hashlib.sha256(data.encode('UTF-8')).hexdigest()
        self.assertEqual(md5, art2['blob']['md5'])
        self.assertEqual(sha1, art2['blob']['sha1'])
        self.assertEqual(sha256, art2['blob']['sha256'])

        # Do you think we should add the following: ?
        # download artifact via admin

        # try to download blob via different user
