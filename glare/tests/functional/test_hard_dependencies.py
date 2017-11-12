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

    def _assert_get_hard_dependencies(self, art_list,
                                      expected_of_hard_dep_nodes_list,
                                      expected_of_hard_dep_edges_list):
        """"assert the function get_hard_dependencies returns the expected
         response. assert by nodes number (nodes) and by dependencies num
         (edges)."""

        art_num = len(art_list)
        self.assertEqual(art_num, len(expected_of_hard_dep_nodes_list))
        for i in range(art_num):
            if expected_of_hard_dep_nodes_list[i] is None:
                self.get(url="/dependencies/%s" % art_list[i]["id"],
                         status=404)
            else:
                graph = self.get(url="/dependencies/%s" %
                                     art_list[i]["id"])["graph"]
                self.assertEqual(expected_of_hard_dep_nodes_list[i],
                                 len(graph["artifacts"]))
                self.assertEqual(expected_of_hard_dep_edges_list[i],
                                 len(graph["dependencies"]))

    def test_hard_dependencies_basic(self):
        # Create artifacts (sample_artifact type)
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

        # assert that we got the expected dependencies
        deps1 = self.get(url="/dependencies/%s" % art_list[1]["id"])["graph"]
        self.assertEqual(len(deps1["artifacts"]), 3)

        self._assert_get_hard_dependencies(art_list, [4, 3, 0, 1, 0],
                                           [4, 3, 0, 1, 0])

        # Delete H.D
        values = {"source_id": art_list[1]['id'],
                  "target_id": art_list[2]['id']}

        self.delete(url="/dependencies/%(source_id)s/%(target_id)s" % values)

        # Make sure we got the expected number of dependencies
        self._assert_get_hard_dependencies(art_list, [3, 2, 0, 1, 0],
                                           [3, 2, 0, 1, 0])

        # Delete nonexisted H.D
        self.delete(url="/dependencies/%(source_id)s/%(target_id)s"
                        % values, status=400)

        # delete art0
        self.delete('/sample_artifact/%s' % art_list[0]['id'])
        self._assert_get_hard_dependencies(art_list, [None, 2, 0, 1, 0],
                                           [None, 2, 0, 1, 0])
