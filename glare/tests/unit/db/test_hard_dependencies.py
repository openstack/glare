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

from glare.db.sqlalchemy import api
from glare.tests.unit import base


class TestHardDependeciesFunctions(base.BaseTestArtifactAPI):
    """Test hard dependencies db functions."""

    def setUp(self):
        super(TestHardDependeciesFunctions, self).setUp()
        self.session = api.get_session()

    def test_get_and_set_hard_dependencies(self):
        #  check that we don't have hard dependencies

        art = self.controller.create(self.req, "images", {'name': "my_img"})
        # initially there are hard dependencies
        self.assertEqual({'graph': {'artifacts': [], 'dependencies': []}},
                         api.get_hard_dependencies(self.req.context,
                                                   art['id'], self.session))

        art_list = []
        for i in range(5):
            art_list.append(
                self.controller.create(self.req, "images",
                                       {'name': "my_img%d" % i}))
        api.set_hard_dependencies(self.req.context, art_list[0]['id'],
                                  art_list[1]['id'], self.session)
        api.set_hard_dependencies(self.req.context, art_list[1]['id'],
                                  art_list[2]['id'], self.session)
        api.set_hard_dependencies(self.req.context, art_list[1]['id'],
                                  art_list[3]['id'], self.session)
        api.set_hard_dependencies(self.req.context, art_list[3]['id'],
                                  art_list[4]['id'], self.session)

        # The graph: art0->art1->art3->art4 , art0->art1->art2
        hard_dep_list_graph_0 = api.get_hard_dependencies(
            self.req.context, art_list[0]['id'], self.session)["graph"]
        hard_dep_list_0_nodes = hard_dep_list_graph_0["artifacts"]
        hard_dep_list_0_edges = hard_dep_list_graph_0["dependencies"]

        self.assertEqual(len(hard_dep_list_0_edges), 4)
        self.assertEqual(len(hard_dep_list_0_nodes), 4)

        hard_dep_list_graph_1 = api.get_hard_dependencies(
            self.req.context, art_list[1]['id'], self.session)["graph"]
        hard_dep_list_1_nodes = hard_dep_list_graph_1["artifacts"]
        hard_dep_list_1_edges = hard_dep_list_graph_1["dependencies"]

        self.assertEqual(len(hard_dep_list_1_edges), 3)
        self.assertEqual(len(hard_dep_list_1_nodes), 3)

        # Delete art1->art2 H.D (Hard dependency)
        api.delete_hard_dependencies(self.req.context, art_list[1]['id'],
                                     art_list[2]['id'], self.session)
        # Get H.D for art1
        hard_dep_list_graph_1 = api.get_hard_dependencies(
            self.req.context, art_list[1]['id'], self.session)["graph"]
        self.assertEqual(len(hard_dep_list_graph_1["artifacts"]), 2)
        self.assertEqual(len(hard_dep_list_graph_1["dependencies"]), 2)
