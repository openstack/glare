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
from glare.tests import sample_artifact
from glare.db.sqlalchemy import api
from glare.tests.unit import base

import random


class TestHardDependencies(base.BaseTestArtifactAPI):

    def test_hard_dependencies(self):
        # Create a bunch of artifacts for list testing
        art_list = []
        for i in range(5):
            art_list.append(
                self.controller.create(self.req, "sample_artifact",
                                       {'name': "my_img%d" % i}))
        self.controller.set_hard_dependencies(art_list[0]['id'],
                                  art_list[1]['id'], self.session)
        self.controller.set_hard_dependencies(art_list[1]['id'],
                                  art_list[2]['id'], self.session)
        self.controller.set_hard_dependencies(art_list[1]['id'],
                                  art_list[3]['id'], self.session)
        self.controller.set_hard_dependencies(art_list[3]['id'],
                                  art_list[4]['id'], self.session)

        # The graph: art0->art1->art3->art4 , art0->art1->art2
        hard_dep_list_0 = self.controller.get_hard_dependencies(
            art_list[0]['id'], self.session)
        self.assertEqual(len(hard_dep_list_0), 4)

        hard_dep_list_1 = self.controller.get_hard_dependencies(
            art_list[1]['id'], self.session)
        self.assertEqual(len(hard_dep_list_1), 3)

        # Delete art1-> art2 H.D (Hard dependency)
        self.controller.delete_hard_dependencies(art_list[1]['id'], art_list[2]['id'], self.session)
        # Get H.D for art1
        hard_dep_list_1 = self.controller.get_hard_dependencies(
            art_list[1]['id'], self.session)
        self.assertEqual(len(hard_dep_list_1), 2)




        # Todo - add tests
