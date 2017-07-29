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

from glare.common import exception
from glare.db.sqlalchemy import api
from glare.tests.unit import base


class TestQuotaFunctions(base.BaseTestArtifactAPI):
    """Test quota db functions."""

    def setUp(self):
        super(TestQuotaFunctions, self).setUp()
        self.session = api.get_session()

    def test_count_artifact_number(self):
        # initially there are no artifacts
        self.assertEqual(0, api.count_artifact_number(
            self.req.context, self.session))

        # create 5 images, 3 heat templates, 2 murano packages and 7 samples
        amount = {
            'images': 5,
            'heat_templates': 3,
            'murano_packages': 2,
            'sample_artifact': 7
        }
        for type_name in amount:
            for num in range(amount[type_name]):
                self.controller.create(
                    self.req, type_name, {'name': type_name + str(num)})

        # create 1 artifact of each type from different user
        req = self.get_fake_request(self.users['user2'])
        for type_name in amount:
            self.controller.create(req, type_name, {'name': type_name})

        # count numbers for each type
        for type_name in amount:
            num = api.count_artifact_number(
                self.req.context, self.session, type_name)
            self.assertEqual(amount[type_name], num)

        # count the whole amount of artifacts
        self.assertEqual(17, api.count_artifact_number(
            self.req.context, self.session))

    def test_calculate_uploaded_data(self):
        # initially there is no data
        self.assertEqual(0, api.calculate_uploaded_data(
            self.req.context, self.session))

        # create a sample artifact
        art1 = self.controller.create(
            self.req, 'sample_artifact', {'name': 'art1'})

        # upload 10 bytes to 'blob'
        self.controller.upload_blob(
            self.req, 'sample_artifact', art1['id'], 'blob',
            BytesIO(b'a' * 10), 'application/octet-stream')
        self.assertEqual(10, api.calculate_uploaded_data(
            self.req.context, self.session))

        # upload 3 blobs to dict_of_blobs with 25, 35 and 45 bytes respectively
        self.controller.upload_blob(
            self.req, 'sample_artifact', art1['id'], 'dict_of_blobs/blob1',
            BytesIO(b'a' * 25), 'application/octet-stream')
        self.controller.upload_blob(
            self.req, 'sample_artifact', art1['id'], 'dict_of_blobs/blob2',
            BytesIO(b'a' * 35), 'application/octet-stream')
        self.controller.upload_blob(
            self.req, 'sample_artifact', art1['id'], 'dict_of_blobs/blob3',
            BytesIO(b'a' * 45), 'application/octet-stream')
        self.assertEqual(115, api.calculate_uploaded_data(
            self.req.context, self.session))

        # create another sample artifact and upload 100 bytes there
        art2 = self.controller.create(
            self.req, 'sample_artifact', {'name': 'art2'})
        self.controller.upload_blob(
            self.req, 'sample_artifact', art2['id'], 'blob',
            BytesIO(b'a' * 100), 'application/octet-stream')
        self.assertEqual(215, api.calculate_uploaded_data(
            self.req.context, self.session))

        # create image and upload 150 bytes there
        img1 = self.controller.create(
            self.req, 'images', {'name': 'img1'})
        self.controller.upload_blob(
            self.req, 'images', img1['id'], 'image',
            BytesIO(b'a' * 150), 'application/octet-stream')
        # the whole amount of uploaded data is 365 bytes
        self.assertEqual(365, api.calculate_uploaded_data(
            self.req.context, self.session))
        # 215 bytes for sample_artifact
        self.assertEqual(215, api.calculate_uploaded_data(
            self.req.context, self.session, 'sample_artifact'))
        # 150 bytes for images
        self.assertEqual(150, api.calculate_uploaded_data(
            self.req.context, self.session, 'images'))

        # create an artifact from another user and check that it's not included
        # for the original user
        req = self.get_fake_request(self.users['user2'])
        another_art = self.controller.create(
            req, 'sample_artifact', {'name': 'another'})
        # upload 1000 bytes to 'blob'
        self.controller.upload_blob(
            req, 'sample_artifact', another_art['id'], 'blob',
            BytesIO(b'a' * 1000), 'application/octet-stream')

        # original user still has 365 bytes
        self.assertEqual(365, api.calculate_uploaded_data(
            self.req.context, self.session))
        # user2 has 1000
        self.assertEqual(
            1000, api.calculate_uploaded_data(req.context, self.session))

    def test_quota_crud_db_operations(self):
        # create several quotas
        q1 = api.create_quota(project_id='project1',
                              quota_name='max_uploaded_data',
                              quota_value=1000, session=self.session)
        self.assertEqual('project1', q1['project_id'])
        self.assertEqual('max_uploaded_data', q1['quota_name'])
        self.assertEqual(1000, q1['quota_value'])
        self.assertIsNone(q1['type_name'])
        self.assertIsNotNone(q1['id'])
        q2 = api.create_quota(project_id='project1',
                              quota_name='max_uploaded_data',
                              quota_value=500,
                              type_name='images', session=self.session)
        self.assertEqual('project1', q2['project_id'])
        self.assertEqual('max_uploaded_data', q2['quota_name'])
        self.assertEqual(500, q2['quota_value'])
        self.assertEqual('images', q2['type_name'])
        self.assertIsNotNone(q2['id'])
        q3 = api.create_quota(project_id='project1',
                              quota_name='max_artifact_number',
                              quota_value=10, session=self.session)
        self.assertEqual('project1', q3['project_id'])
        self.assertEqual('max_artifact_number', q3['quota_name'])
        self.assertEqual(10, q3['quota_value'])
        self.assertIsNone(q3['type_name'])
        self.assertIsNotNone(q3['id'])

        # creation of another quota with the same parameters fails
        self.assertRaises(
            exception.Conflict, api.create_quota,
            project_id='project1', quota_name='max_artifact_number',
            quota_value=10, session=self.session)

        # update quota with new parameters
        q3 = api.update_quota('project1', q3['id'], 20, self.session)
        self.assertEqual('project1', q3['project_id'])
        self.assertEqual('max_artifact_number', q3['quota_name'])
        self.assertEqual(20, q3['quota_value'])
        self.assertIsNone(q1['type_name'])
        self.assertIsNotNone(q3['id'])

        # if quota doesn't exist - raise NotFound
        self.assertRaises(exception.NotFound, api.update_quota, 'project1',
                          "INVALID_ID", 100, self.session)

        # if quota doesn't exist for project - raise NotFound
        self.assertRaises(exception.NotFound, api.update_quota,
                          'INVALID_PROJECT', q3['id'], 100, self.session)

        # get quota information
        q_get = api.get_quota('project1', q3['id'], self.session)
        self.assertEqual(q3, q_get)

        # if quota doesn't exist for project - raise NotFound
        self.assertRaises(exception.NotFound, api.get_quota,
                          'INVALID_PROJECT', q3['id'], self.session)

        # delete quota
        api.delete_quota('project1', q3['id'], self.session)
        self.assertRaises(exception.NotFound, api.get_quota,
                          'project1', q3['id'], self.session)

        # if quota doesn't exist for project - raise NotFound
        self.assertRaises(exception.NotFound, api.delete_quota,
                          'INVALID_PROJECT', q3['id'], self.session)

        # can create the the same quota again
        q3 = api.create_quota(project_id='project1',
                              quota_name='max_artifact_number',
                              quota_value=10, session=self.session)
        self.assertEqual('project1', q3['project_id'])
        self.assertEqual('max_artifact_number', q3['quota_name'])
        self.assertEqual(10, q3['quota_value'])
        self.assertIsNone(q3['type_name'])
        self.assertIsNotNone(q3['id'])

        # deletion of non-existing quota fails
        self.assertRaises(exception.NotFound, api.delete_quota,
                          'project1', "INVALID_ID", self.session)

    def test_list_project_quotas(self):
        # create several quotas
        q1 = api.create_quota(project_id='project1',
                              quota_name='max_uploaded_data',
                              quota_value=1000, session=self.session)
        q2 = api.create_quota(project_id='project1',
                              quota_name='max_uploaded_data',
                              quota_value=500,
                              type_name='images', session=self.session)
        q3 = api.create_quota(project_id='project1',
                              quota_name='max_artifact_number',
                              quota_value=10, session=self.session)
        q4 = api.create_quota(project_id='project2',
                              quota_name='max_uploaded_data',
                              quota_value=1000, session=self.session)
        q5 = api.create_quota(project_id='project2',
                              quota_name='max_uploaded_data',
                              quota_value=500,
                              type_name='sample_artifact',
                              session=self.session)
        q6 = api.create_quota(project_id='project2',
                              quota_name='max_artifact_number',
                              quota_value=20, session=self.session)
        q7 = api.create_quota(project_id='project3',
                              quota_name='max_uploaded_data',
                              quota_value=1000, session=self.session)

        project1_quotas = api.get_all_project_quotas('project1', self.session)
        self.assertEqual(3, len(project1_quotas))
        for q in (q1, q2, q3):
            self.assertIn(q, project1_quotas)

        project2_quotas = api.get_all_project_quotas('project2', self.session)
        self.assertEqual(3, len(project2_quotas))
        for q in (q4, q5, q6):
            self.assertIn(q, project2_quotas)

        project3_quotas = api.get_all_project_quotas('project3', self.session)
        self.assertEqual(1, len(project3_quotas))
        self.assertIn(q7, project3_quotas)
