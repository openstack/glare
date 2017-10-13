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

from glare.tests.functional import base


class TestExternalAPI(base.TestArtifact):
    """Test external REST API."""

    def setUp(self):
        base.functional.FunctionalTest.setUp(self)

        self.glare_server.deployment_flavor = 'noauth'
        self.glare_server.enabled_artifact_types = ','.join(
            self.enabled_types)
        self.glare_server.custom_artifact_types_modules = (
            'glare.tests.sample_artifact')
        self.glare_server.custom_external_api_modules = (
            'glare.tests.external_all_api')

        self.start_servers(**self.__dict__.copy())

        self.set_user('user1')

    def test_all(self):
        for type_name in self.enabled_types:
            if type_name == 'all':
                continue
            for i in range(3):
                for j in range(3):
                    self.create_artifact(
                        data={'name': '%s_%d' % (type_name, i),
                              'version': '%d' % j,
                              'tags': ['tag%s' % i]},
                        type_name=type_name)

        # get all possible artifacts
        url = '/all_artifacts?sort=name:asc&limit=100'
        res = self.get(url=url, status=200)['artifacts']
        self.assertEqual(54, len(res))

        # get artifacts with latest versions
        url = '/all_artifacts?version=latest&sort=name:asc'
        res = self.get(url=url, status=200)['artifacts']
        self.assertEqual(18, len(res))
        for art in res:
            self.assertEqual('2.0.0', art['version'])

        # get images only
        url = '/all_artifacts?type_name=images&sort=name:asc'
        res = self.get(url=url, status=200)['artifacts']
        self.assertEqual(9, len(res))
        for art in res:
            self.assertEqual('images', art['type_name'])

        # get images and heat_templates
        url = '/all_artifacts?type_name=in:images,heat_templates&sort=name:asc'
        res = self.get(url=url, status=200)['artifacts']
        self.assertEqual(18, len(res))
        for art in res:
            self.assertIn(art['type_name'], ('images', 'heat_templates'))
