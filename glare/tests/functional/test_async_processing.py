# Copyright 2017 - Nokia Networks
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

import time

from glare.tests.functional import base


class TestAsync(base.TestArtifact):
    def setUp(self):
        base.functional.FunctionalTest.setUp(self)

        self.set_user('user1')
        self.glare_server.deployment_flavor = 'noauth'

        self.glare_server.enabled_artifact_types = 'async_artifact'
        self.glare_server.custom_artifact_types_modules = (
            'glare.tests.async_artifact')
        self.start_servers(**self.__dict__.copy())

    def test_async_upload(self):
        data = 'some_arbitrary_testing_data'
        art = self.create_artifact(data={'name': 'test_af',
                                         'version': '0.0.1'},
                                   type_name='async_artifact')
        url = '/async_artifact/%s' % art['id']

        headers = {'Content-Type': 'application/octet-stream'}
        res = self.put(url=url + '/blob', data=data, status=202,
                       headers=headers)
        self.assertTrue(res.startswith(
            'http://127.0.0.1:%d/flows/' % self.glare_server.bind_port))

        art = self.get(url='/async_artifact/%s' % art['id'])
        self.assertEqual('staged', art['blob']['status'])

        time.sleep(10)

        art = self.get(url='/async_artifact/%s' % art['id'])
        self.assertEqual('active', art['blob']['status'])
