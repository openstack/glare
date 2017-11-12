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

from glare.common import exception as exc
from glare.i18n import _
from glare.tests.unit import base
from random import shuffle


class TestHardDependencies(base.BaseTestArtifactAPI):
    def setUp(self):
        super(TestHardDependencies, self).setUp()

    def _create_artifacts(self, art_number):
        art_list = []
        for i in range(art_number):
            art_list.append(
                self.controller.create(self.req, "sample_artifact",
                                       {'name': "my_img%d" % i}))
        return art_list

    def _set_dependencies(self, art_list, dependencies_list,
                          raise_exceptions=False):
        """Set H.D between artifacts
        :param art_list: the created artifact list
        :param dependencies_list: tuple list.
        each tuple contains (source_id,target_id)
        :param raise_exceptions: Boolean. False means we wanna create H.D.
        True means we wanna assert we cannot create H.D.
        """
        h_d_action_num = len(dependencies_list)
        for i in range(h_d_action_num):
            source_indx = dependencies_list[i][0]
            source_id = art_list[source_indx]["id"]
            target_indx = dependencies_list[i][1]
            target_id = art_list[target_indx]["id"]
            if not raise_exceptions:
                self.controller.set_hard_dependencies(self.req, source_id,
                                                      target_id)
            else:  # flag symbolize that we test negative cases
                print("trying to (negative) set H.d from:", source_indx,
                      "to:", target_indx)
                self.assertRaises(exc.BadRequest,
                                  self.controller.set_hard_dependencies,
                                  self.req, source_id, target_id)

    def _negative_assert_set_dependencies(self, art_list, dependencies_list):
        """assert that we CANNOT set the H.D specified by dependencies_list
        :param art_list: the created artifact list
        :param dependencies_list: tuple list.
        each tuple contains (source_id,target_id)
        """
        self._set_dependencies(art_list, dependencies_list,
                               raise_exceptions=True)

    def _assert_get_hard_dependencies_resp(self, art_list,
                                           expected_of_hard_dep_nodes_list,
                                           expected_of_hard_dep_edges_list):
        """assert the function get_hard_dependencies returns the expected
         response. assert by nodes number (nodes) and by dependencies num
         (edges).
         """

        art_num = len(art_list)
        self.assertEqual(art_num, len(expected_of_hard_dep_nodes_list))
        for i in range(art_num):
            art_i = art_list[i]['id']
            if expected_of_hard_dep_nodes_list[i] is None:
                self.assertRaises(exc.ArtifactNotFound,
                                  self.controller.get_hard_dependencies,
                                  self.req, art_i)
            else:
                hard_dep_list = self.controller.get_hard_dependencies(self.req,
                                                                      art_i)
                message = _("expected: %(node_list)s nodes for %(art)d but"
                            " found %(num_nodes)d nodes") % {
                    'node_list': expected_of_hard_dep_nodes_list,
                    'art': i,
                    'num_nodes': len(hard_dep_list["graph"]["artifacts"])}
                self.assertEqual(expected_of_hard_dep_nodes_list[i],
                                 len(hard_dep_list["graph"]["artifacts"]),
                                 message=message)

                message = _("expected: %(edges_list)s nodes for %(art)d but"
                            " found %(num_edges)d nodes") % {
                    'edges_list': expected_of_hard_dep_nodes_list,
                    'art': i,
                    'num_edges': len(hard_dep_list["graph"]["dependencies"])}

                self.assertEqual(expected_of_hard_dep_edges_list[i],
                                 len(hard_dep_list["graph"]["dependencies"]),
                                 message=message)

    def _negative_delete_h_d(self, art_list, tuple_h_d_list):
        """Assert that we CANNOT delete the H.D specified by tuple_h_d_list
        :param art_list: the created artifact list.
        :param tuple_h_d_list: tuple list.
        each tuple contains (source_id,target_id)
        """
        for i in range(len(tuple_h_d_list)):
            source_ind = tuple_h_d_list[i][0]
            target_ind = tuple_h_d_list[i][1]
            print(_("try to delete hard dependency between %(s_art)d to"
                    " %(t_art)d") % {"s_art": source_ind, "t_art": target_ind})
            self.assertRaises(exc.BadRequest,
                              self.controller.delete_hard_dependencies,
                              self.req, art_list[source_ind]['id'],
                              art_list[target_ind]['id'])

    def _assert_hard_dep_children(self, art_list, art_num,
                                  expected_nodes, expected_edges):
        graphs_list = [self.controller.get_hard_dependencies_children(
            self.req, art_list[i]['id'])['graph'] for i in range(art_num)]
        len_nodes_list = [len(graph["artifacts"]) for graph in graphs_list]
        len_edges_list = [len(graph["dependencies"]) for graph in graphs_list]
        self.assertEqual(len_nodes_list, expected_nodes)
        self.assertEqual(len_edges_list, expected_edges)

    def test_hard_dependencies_linear_basic1(self):
        art_num = 5
        art_list = self._create_artifacts(art_num)
        self._set_dependencies(art_list, [(0, 1), (1, 2), (2, 3), (3, 4)])

        # The graph: art0->art1->art2->art3->art4
        cur_dependencies_list = [4, 3, 2, 1, 0]
        self._assert_get_hard_dependencies_resp(art_list,
                                                cur_dependencies_list,
                                                cur_dependencies_list)
        # test hard_dependencies_children_list #
        self._assert_hard_dep_children(art_list, art_num,
                                       expected_nodes=[0, 1, 2, 3, 4],
                                       expected_edges=[0, 1, 2, 3, 4])
        # test cycles #
        negative_h_d_list = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2),
                             (4, 0), (4, 1), (4, 2), (4, 3)]
        self._negative_assert_set_dependencies(art_list, negative_h_d_list)
        # assert that nothing was changed
        self._assert_get_hard_dependencies_resp(art_list,
                                                cur_dependencies_list,
                                                cur_dependencies_list)
        # delete Hard Dependencies #

        # Negative
        tuple_h_d_list = [(1, 0), (0, 2), (2, 1), (2, 4), (3, 0),
                          (3, 1), (3, 2), (4, 0), (4, 1), (4, 2), (4, 3)]
        self._negative_delete_h_d(art_list, tuple_h_d_list)

        # Positive
        for i in range(art_num - 1):
            self.controller.delete_hard_dependencies(self.req,
                                                     art_list[i]['id'],
                                                     art_list[i + 1]['id'])
            # check by the pattern for the linear graph
            cur_dependencies_list[i] = 0  # relevant for both edges and nodes
            self._assert_get_hard_dependencies_resp(art_list,
                                                    cur_dependencies_list,
                                                    cur_dependencies_list)
        # Delete artifact #
        # Make sure we can delete artifact that has no children
        for art in art_list:
            self.controller.delete(self.req, 'sample_artifact', art['id'])

    def test_hard_dependencies_linear_basic2(self):
        art_num = 5
        art_list = self._create_artifacts(art_num)
        self._set_dependencies(art_list, [(2, 3), (3, 4), (1, 2), (0, 1)])

        # The graph: art0->art1->art2->art3->art4
        cur_dependencies_list = [4, 3, 2, 1, 0]
        self._assert_get_hard_dependencies_resp(art_list,
                                                cur_dependencies_list,
                                                cur_dependencies_list)
        # test hard_dependencies_children_list #
        self._assert_hard_dep_children(art_list, art_num,
                                       expected_nodes=[0, 1, 2, 3, 4],
                                       expected_edges=[0, 1, 2, 3, 4])
        # test cycles #
        negative_h_d_list = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2),
                             (4, 0), (4, 1), (4, 2), (4, 3)]
        self._negative_assert_set_dependencies(art_list, negative_h_d_list)
        # assert that nothing was changed
        self._assert_get_hard_dependencies_resp(art_list,
                                                cur_dependencies_list,
                                                cur_dependencies_list)
        # delete Hard Dependencies #

        # Negative
        tuple_h_d_list = [(1, 0), (0, 2), (2, 1), (2, 4), (3, 0),
                          (3, 1), (3, 2), (4, 0), (4, 1), (4, 2), (4, 3)]
        self._negative_delete_h_d(art_list, tuple_h_d_list)

        # Positive
        for i in range(art_num - 1):
            self.controller.delete_hard_dependencies(self.req,
                                                     art_list[i]['id'],
                                                     art_list[i + 1]['id'])
            # check by the pattern for the linear graph
            cur_dependencies_list[i] = 0  # relevant for both edges and nodes
            self._assert_get_hard_dependencies_resp(art_list,
                                                    cur_dependencies_list,
                                                    cur_dependencies_list)
        # Delete artifacts #
        # Make sure we can delete artifact that has no children
        for art in art_list:
            self.controller.delete(self.req, 'sample_artifact', art['id'])

    def test_hard_dependencies_basic2(self):
        art_num = 5

        # Create a bunch of artifacts H.D graph
        art_list = self._create_artifacts(art_num)

        self._set_dependencies(art_list, [(0, 1), (1, 2), (1, 3), (3, 4)])

        # The graph: art0->art1->art3->art4 , art0->art1->art2
        self._assert_get_hard_dependencies_resp(art_list, [4, 3, 0, 1, 0],
                                                [4, 3, 0, 1, 0])
        # test hard_dependencies_children_list #
        self._assert_hard_dep_children(art_list, art_num,
                                       expected_nodes=[0, 1, 2, 2, 3],
                                       expected_edges=[0, 1, 2, 2, 3])

        # Delete art1-> art2 H.D (Hard dependency)
        self.controller.delete_hard_dependencies(self.req, art_list[1]['id'],
                                                 art_list[2]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [3, 2, 0, 1, 0],
                                                [3, 2, 0, 1, 0])

        # Make sure we can delete artifact that has no children
        # (even if it has H.D to other artifact)
        for art in art_list:
            self.controller.delete(self.req, 'sample_artifact', art['id'])

    def test_hard_dependencies_cycles_basic(self):
        # The graph: 2<-0->1->3->2
        art_num = 4
        art_list = self._create_artifacts(art_num)

        # Set Dependencies
        dependencies_list = [(0, 1), (1, 2), (0, 2), (1, 3), (3, 2)]
        self._set_dependencies(art_list, dependencies_list)

        negative_h_d_list = [(0, 0), (1, 1), (2, 2), (3, 3), (1, 0),
                             (2, 0), (2, 1), (2, 3), (3, 0), (3, 1)]
        self._negative_assert_set_dependencies(art_list, negative_h_d_list)
        self._assert_get_hard_dependencies_resp(art_list, [3, 2, 0, 1],
                                                [5, 3, 0, 1])

    def test_hard_dependencies_deletions(self):
        """test artifact deletions and H.D deletions scenarios"""
        art_num = 5
        art_list = self._create_artifacts(art_num)

        # Set Dependencies
        self._set_dependencies(art_list, [(0, 2), (1, 2), (2, 3), (2, 4)])
        # The graph: art0->art2<-art1, art3<-art2->art4

        # Assert that the graph was built successfully
        self._assert_get_hard_dependencies_resp(art_list, [3, 3, 2, 0, 0],
                                                [3, 3, 2, 0, 0])
        # Negative art deletion

        # Negative art4 deletion - art2 has H.D to art4
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[3]['id'])

        # Negative art3 deletion - art2 has H.D to art3
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[3]['id'])

        # Negative art2 deletion - art0 and art1 have H.D to art2
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[2]['id'])

        # Make sure nothing has changed
        self._assert_get_hard_dependencies_resp(art_list, [3, 3, 2, 0, 0],
                                                [3, 3, 2, 0, 0])

        # Negative H.D deletion - delete nonexistent H.D
        tuple_h_d_list = [(0, 1), (1, 0), (2, 0), (2, 1),
                          (3, 2), (4, 2), (3, 4), (4, 3)]
        self._negative_delete_h_d(art_list, tuple_h_d_list)

        # Positive H.D deletions

        # Delete art2->art4 H.D
        self.controller.delete_hard_dependencies(self.req, art_list[2]['id'],
                                                 art_list[4]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [2, 2, 1, 0, 0],
                                                [2, 2, 1, 0, 0])
        # Delete art0->art2 H.D
        self.controller.delete_hard_dependencies(self.req, art_list[0]['id'],
                                                 art_list[2]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [0, 2, 1, 0, 0],
                                                [0, 2, 1, 0, 0])

        # Delete art2->art3 H.D
        self.controller.delete_hard_dependencies(self.req, art_list[2]['id'],
                                                 art_list[3]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [0, 1, 0, 0, 0],
                                                [0, 1, 0, 0, 0])

        # Delete art1->art2 H.D
        self.controller.delete_hard_dependencies(self.req, art_list[1]['id'],
                                                 art_list[2]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [0, 0, 0, 0, 0],
                                                [0, 0, 0, 0, 0])

        # Now make sure we can delete all the artifacts
        for art in art_list:
            self.controller.delete(self.req, 'sample_artifact', art['id'])

    def test_hard_dependencies_complex_graph_1(self):
        # The graph will be: art4<-art1<-art0->art2<-art3<-art1,
        #  art0->art4<-art2
        art_num = 5
        art_list = self._create_artifacts(art_num)
        # Set Dependencies
        dependencies_list = [(0, 1), (1, 3), (3, 2), (0, 2),
                             (0, 4), (1, 4), (2, 4)]
        self._set_dependencies(art_list, dependencies_list)
        self._assert_get_hard_dependencies_resp(art_list, [4, 3, 1, 2, 0],
                                                [7, 4, 1, 2, 0])
        # Negative art deletion

        # Negative art1 deletion - art1 has H.D to art0
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[1]['id'])

        # Negative art2 deletion - art3 has H.D to art2
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[2]['id'])

        # Negative art3 deletion - art0,art1 have H.D to art3
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[3]['id'])

        # Negative art4 deletion - art0,art1,art2 have H.D to art4
        self.assertRaises(exc.Forbidden, self.controller.delete,
                          self.req, 'sample_artifact',
                          art_list[4]['id'])

        # Cycles testing #
        negative_h_d_list = [(1, 0), (2, 0), (2, 1), (2, 3), (3, 0),
                             (3, 1), (4, 0), (4, 1), (4, 2), (4, 3)]
        self._negative_assert_set_dependencies(art_list, negative_h_d_list)

        # test hard_dependencies_children_list #
        self._assert_hard_dep_children(art_list, art_num,
                                       expected_nodes=[0, 1, 3, 2, 4],
                                       expected_edges=[0, 1, 4, 2, 7])

        # Positive art deletion #
        self.controller.delete(self.req, 'sample_artifact', art_list[0]['id'])
        self._assert_get_hard_dependencies_resp(art_list, [None, 3, 1, 2, 0],
                                                [None, 4, 1, 2, 0])

        self.controller.delete(self.req, 'sample_artifact', art_list[1]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [None, None, 1, 2, 0],
                                                [None, None, 1, 2, 0])

        self.controller.delete(self.req, 'sample_artifact', art_list[3]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [None, None, 1, None, 0],
                                                [None, None, 1, None, 0])

        self.controller.delete(self.req, 'sample_artifact', art_list[2]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [None, None, None, None, 0],
                                                [None, None, None, None, 0])

        self.controller.delete(self.req, 'sample_artifact', art_list[4]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [None, None, None, None, None],
                                                [None, None, None, None, None])

    def test_hard_dependencies_complex_graph_2(self):
        # The graph will be: 4->0->1->2->3->5->6, 2->5
        art_num = 7
        art_list = self._create_artifacts(art_num)

        # Set Dependencies
        dependencies_list = [(3, 5), (4, 0), (2, 3),
                             (0, 1), (2, 5), (5, 6), (1, 2)]
        # make sure that H.D setting order doesn't matter
        shuffle(dependencies_list)
        print("the shuffled dependencies_list:", dependencies_list)
        self._set_dependencies(art_list, dependencies_list)

        self._assert_get_hard_dependencies_resp(art_list,
                                                [5, 4, 3, 2, 6, 1, 0],
                                                [6, 5, 4, 2, 7, 1, 0])

        # Negative H.D setting #

        # Cycles testing #
        negative_cycles_h_d_list = [(6, 5), (6, 3), (6, 2), (6, 1), (6, 0),
                                    (6, 4), (5, 3), (5, 2), (5, 1), (5, 0),
                                    (5, 4), (4, 4), (3, 2), (3, 1), (3, 0),
                                    (3, 4), (2, 1), (2, 0), (1, 0), (1, 4)]
        # negative_h_d_list = dependencies_list + negative_cycles_h_d_list
        #  Todo(Idan) replace negative_cycles_h_d_list with negative_h_d_list
        self._negative_assert_set_dependencies(art_list,
                                               negative_cycles_h_d_list)

        # hard_dependencies_children_list testing #
        self._assert_hard_dep_children(art_list, art_num,
                                       expected_nodes=[1, 2, 3, 4, 0, 5, 6],
                                       expected_edges=[1, 2, 3, 4, 0, 9, 6])
        # Delete artifact #
        # Negative
        for i in range(art_num):
            if i != 4:  # art4 deletion is valid
                self.assertRaises(exc.Forbidden, self.controller.delete,
                                  self.req, 'sample_artifact',
                                  art_list[i]['id'])
        # Positive
        self.controller.delete(self.req, 'sample_artifact', art_list[4]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [5, 4, 3, 2, None, 1, 0],
                                                [6, 5, 4, 2, None, 1, 0])
        for i in range(art_num):
            if i != 4:  # art4 was deleted already
                self.controller.delete(self.req, 'sample_artifact',
                                       art_list[i]['id'])

    def test_hard_dependencies_complex_graph_3(self):
        # The graph will be:
        art_num = 8
        art_list = self._create_artifacts(art_num)

        # Set Dependencies
        dependencies_list = [(0, 5), (1, 5), (2, 5), (3, 4), (4, 5),
                             (6, 0), (2, 3), (0, 1), (1, 2), (5, 7)]
        # make sure that H.D setting order doesn't matter
        shuffle(dependencies_list)
        print("the shuffled dependencies_list:", dependencies_list)
        self._set_dependencies(art_list, dependencies_list)

        expected_h_d_nodes = [6, 5, 4, 3, 2, 1, 7, 0]
        expected_h_d_edges = [9, 7, 5, 3, 2, 1, 10, 0]
        self._assert_get_hard_dependencies_resp(art_list,
                                                expected_h_d_nodes,
                                                expected_h_d_edges)
        # Negative H.D setting #

        # Cycles testing #
        neg_cyc_to_node_7 = [(7, i) for i in range(7)]
        neg_cyc_to_node_5 = [(5, i) for i in range(7)]
        negative_cycles_h_d_list = neg_cyc_to_node_7 + neg_cyc_to_node_5 +\
            [(4, 0), (4, 2), (4, 3), (4, 6),
             (3, 0), (3, 1), (3, 2), (3, 6),
             (2, 1), (2, 0), (2, 6), (1, 0), (1, 6)]
        # negative_h_d_list = dependencies_list + negative_cycles_h_d_list
        # Todo(idan) replace negative_cycles_h_d_list with negative_h_d_list
        self._negative_assert_set_dependencies(art_list,
                                               negative_cycles_h_d_list)

        # # hard_dependencies_children_list testing #
        self._assert_hard_dep_children(art_list, art_num,
                                       [1, 2, 3, 4, 5, 6, 0, 7],
                                       [1, 2, 3, 4, 5, 15, 0, 7])
        # Delete artifact #
        # Negative
        for i in range(art_num):
            if i != 6:  # art6 deletion is valid
                self.assertRaises(exc.Forbidden, self.controller.delete,
                                  self.req, 'sample_artifact',
                                  art_list[i]['id'])
        # Positive
        self.controller.delete(self.req, 'sample_artifact', art_list[6]['id'])
        self._assert_get_hard_dependencies_resp(art_list,
                                                [6, 5, 4, 3, 2, 1, None, 0],
                                                [9, 7, 5, 3, 2, 1, None, 0])
        for i in range(art_num):
            if i != 6:  # art6 was deleted already
                self.controller.delete(self.req, 'sample_artifact',
                                       art_list[i]['id'])
