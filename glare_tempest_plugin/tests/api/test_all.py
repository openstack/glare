# Copyright (c) 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools

from glare_tempest_plugin.tests.api import base
from pprint import pformat
from tempest import config
from tempest.lib import exceptions as exc

CONF = config.CONF


class TestAll(base.BaseArtifactTest):

    @testtools.testcase.attr('TestListSanity')
    def test_all(self):
        #  Todo: add sample_artifact
        for type_name in ["heat_environments", "heat_templates",
                          "images", "murano_packages", "tosca_templates"]:
            if type_name == 'all':
                continue
            for i in range(3):
                for j in range(3):
                    self.artifacts_client.create_artifact(
                        type_name=type_name, name='%s_%d' % (type_name, i),
                        version='%d' % j)

        # get all possible artifacts
        res = self.artifacts_client.list_artifacts('all')
        expect_art_num = 25  # Todo: analayze the expected_art_num
        self.assertEqual(expect_art_num, len(res[u'all']),
                         pformat(res[u'all']))
        #  Got: 7 images, 9 tosca_templates, 9 murano_packages

        # get artifacts with latest versions
        url = '?version=latest&sort=name:asc'
        res = self.artifacts_client.list_artifacts('all', uri=url)["all"]

        # Todo: analayze 15
        self.assertEqual(15, len(res), pformat(res))
        for art in res:
            self.assertEqual(u'2.0.0', art["version"], pformat(res))

        # get images only
        url = '?type_name=images&sort=name:asc'
        res = self.artifacts_client.list_artifacts('all', uri=url)['all']

        self.assertEqual(9, len(res))
        for art in res:
            self.assertEqual('images', art['type_name'])

        # get images and tosca_templates
        url = '?type_name=in:images,tosca_templates,' \
              'murano_packages&sort=name:asc'
        res = self.artifacts_client.list_artifacts('all', uri=url)['all']
        self.assertEqual(25, len(res))
        # todo: analayze do we have 25 and not 27?
        for art in res:
            self.assertIn(art['type_name'],
                          ('images', 'tosca_templates', 'murano_packages'))

        url = '?type_name=in:heat_environments,heat_templates&sort=name:asc'
        res = self.artifacts_client.list_artifacts('all', uri=url)['all']
        self.assertEqual(18, len(res))
        for art in res:
            self.assertIn(art['type_name'], ('heat_environments',
                                             'heat_templates'))

    @testtools.testcase.attr('TestUpdateSanity')
    def test_all_readonlyness(self):
        self.assertRaises(exc.Forbidden, self.artifacts_client.create_artifact,
                          type_name='all', name='invalid_type')

        art = self.artifacts_client.create_artifact(name='image',
                                                    type_name='images')

        # update 'all' is forbidden
        self.assertRaises(exc.Forbidden, self.artifacts_client.update_artifact,
                          type_name='all', art_id=art['id'],
                          description='newnewname')

        # activation is forbidden
        self.assertRaises(exc.Forbidden, self.artifacts_client.update_artifact,
                          type_name='all', art_id=art['id'], status='active')

        # publishing is forbidden
        self.assertRaises(exc.Forbidden, self.artifacts_client.update_artifact,
                          type_name='all', art_id=art['id'],
                          visibility='public')

        # get to 'all' is okay
        new_art = self.artifacts_client.get_artifact('all', art['id'])
        self.assertEqual(new_art['id'], art['id'])
