# Copyright 2016 OpenStack Foundation
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

from glare.tests.functional import base


class TestHardDependencies(base.TestArtifact):
    def test_list_marker_and_limit(self):
        # Create artifacts
        art_list = [self.create_artifact({'name': 'name%s' % i})
                    for i in range(5)]

        url = '/dependencies'
        # Set hard dependencies between artifacts
        values = {"source_id": art_list[0]['id'],
                  "target_id": art_list[1]['id']}
        self.post(url=url, data=values, status=204)

        values = {"source_id": art_list[1]['id'],
                  "target_id": art_list[2]['id']}
        self.post(url=url, data=values, status=204)

        values = {"source_id": art_list[1]['id'],
                  "target_id": art_list[3]['id']}
        self.post(url=url, data=values, status=204)

        values = {"source_id": art_list[3]['id'],
                  "target_id": art_list[4]['id']}
        self.post(url=url, data=values, status=204)

        # The graph: art0->art1->art3->art4 , art0->art1->art2

        # Get H.D (Hard dependencies) for the first art in the list
        deps0 = self.get(url="/dependencies/%s" % art_list[0]["id"])
        # assert that we got the expected dependencies
        self.assertEqual(len(deps0), 4)
        # Get H.D for the second artifact
        deps1 = self.get(url="/dependencies/%s" % art_list[1]["id"])
        self.assertEqual(len(deps1), 3)
        # Delete H.D
        values = {"source_id": art_list[1]['id'],
                  "target_id": art_list[2]['id']}
        self.delete(url="/dependencies/%(source_id)s/%(target_id)s" % values)
        deps1 = self.get(url="/dependencies/%s" % art_list[1]["id"])
        # Make sure we got the expected number of dependencies
        self.assertEqual(len(deps1), 2)

        # Delete not existed H.D
        self.delete(url="/dependencies/%(source_id)s/%(target_id)s" % values,
                    status=400)
