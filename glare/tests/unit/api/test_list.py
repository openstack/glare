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
from glare.tests.unit import base


class TestArtifactList(base.BaseTestArtifactAPI):
    def test_list_simple_fields(self):
        # Create a bunch of artifacts for list testing
        values = [
            {'name': 'art1', 'version': '0.0.1', 'string_required': 'str1',
             'int1': 5, 'float1': 5.0, 'bool1': 'yes'},
            {'name': 'art1', 'version': '1-beta', 'string_required': 'str2',
             'int1': 6, 'float1': 6.0, 'bool1': 'yes'},
            {'name': 'art1', 'version': '1', 'string_required': 'str1',
             'int1': 5, 'float1': 5.0, 'bool1': 'no', 'description': 'ggg'},
            {'name': 'art1', 'version': '2-rc1', 'string_required': 'str22',
             'int1': 7, 'float1': 7.0, 'bool1': 'yes'},
            {'name': 'art1', 'version': '10', 'string_required': 'str222',
             'int1': 5, 'float1': 5.0, 'bool1': 'yes'},
            {'name': 'art2', 'version': '1', 'string_required': 'str1',
             'int1': 8, 'float1': 8.0, 'bool1': 'no'},
            {'name': 'art3', 'version': '1', 'string_required': 'str1',
             'int1': -5, 'float1': -5.0, 'bool1': 'yes'},
        ]
        arts = [self.controller.create(self.req, 'sample_artifact', val)
                for val in values]

        # Activate 3rd and 4th artifacts
        changes = [{'op': 'replace', 'path': '/status', 'value': 'active'}]
        arts[3] = self.update_with_values(changes, art_id=arts[3]['id'])
        arts[4] = self.update_with_values(changes, art_id=arts[4]['id'])

        # Publish 4th artifact
        changes = [{'op': 'replace', 'path': '/visibility', 'value': 'public'}]
        self.req = self.get_fake_request(user=self.users['admin'])
        arts[4] = self.update_with_values(changes, art_id=arts[4]['id'])
        self.req = self.get_fake_request(user=self.users['user1'])

        # Do tests basic tests
        # input format for filters is a list of tuples:
        # (filter_name, filter_value)

        # List all artifacts
        res = self.controller.list(self.req, 'sample_artifact', [])
        self.assertEqual(7, len(res['artifacts']))
        self.assertEqual('sample_artifact', res['type_name'])

        # Filter by name
        filters = [('name', 'art1')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(5, len(res['artifacts']))

        # Filter by string_required
        filters = [('string_required', 'str1')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(4, len(res['artifacts']))
        for i in (0, 2, 5, 6):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by int1
        filters = [('int1', '5')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 4):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by float1
        filters = [('float1', '5.0')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 4):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by bool1
        filters = [('bool1', 'yes')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(5, len(res['artifacts']))
        for i in (0, 1, 3, 4, 6):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by id
        filters = [('id', arts[0]['id'])]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(1, len(res['artifacts']))
        self.assertIn(arts[0], res['artifacts'])

        # Filter by status
        filters = [('status', 'active')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(2, len(res['artifacts']))
        for i in (3, 4):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by visibility
        filters = [('visibility', 'public')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(1, len(res['artifacts']))
        self.assertIn(arts[4], res['artifacts'])

        # Filter by owner
        filters = [('owner', arts[0]['owner'])]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(7, len(res['artifacts']))
        for i in range(6):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by description leads to BadRequest
        filters = [('description', 'ggg')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Filter by created_at with eq operator leads to BadRequest
        filters = [('created_at', arts[4]['created_at'])]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Filter by updated_at with eq operator leads to BadRequest
        filters = [('updated_at', arts[4]['updated_at'])]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Filter by activated_at with eq operator leads to BadRequest
        filters = [('activated_at', arts[4]['activated_at'])]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Filter by any blob leads to BadRequest
        filters = [('blob', 'something')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

    def test_list_compound_fields(self):
        # Create a bunch of artifacts for list testing
        values = [
            {'name': 'art1',
             'dict_of_str': {'a': 'aa', 'b': 'bb'},
             'dict_of_int': {'one': 1, 'two': 2},
             'list_of_str': ['aa', 'bb'],
             'list_of_int': [1, 2]},
            {'name': 'art2',
             'dict_of_str': {'b': 'bb', 'c': 'cc'},
             'dict_of_int': {'two': 2, 'three': 3},
             'list_of_str': ['bb', 'cc'],
             'list_of_int': [2, 3]},
            {'name': 'art3',
             'dict_of_str': {'a': 'aa', 'c': 'cc'},
             'dict_of_int': {'one': 1, 'three': 3},
             'list_of_str': ['aa', 'cc'],
             'list_of_int': [1, 3]},
            {'name': 'art4',
             'dict_of_str': {'a': 'bb'},
             'dict_of_int': {'one': 2},
             'list_of_str': ['aa'],
             'list_of_int': [1]},
            {'name': 'art5',
             'dict_of_str': {'b': 'bb'},
             'dict_of_int': {'two': 2},
             'list_of_str': ['bb'],
             'list_of_int': [2]},
            {'name': 'art6',
             'dict_of_str': {},
             'dict_of_int': {},
             'list_of_str': [],
             'list_of_int': []},
        ]
        arts = [self.controller.create(self.req, 'sample_artifact', val)
                for val in values]

        # List all artifacts
        res = self.controller.list(self.req, 'sample_artifact', [])
        self.assertEqual(6, len(res['artifacts']))
        self.assertEqual('sample_artifact', res['type_name'])

        # Return artifacts that contain key 'a' in 'dict_of_str'
        filters = [('dict_of_str', 'eq:a')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain key 'a' or 'c' in 'dict_of_str'
        filters = [('dict_of_str', 'in:a,c')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(4, len(res['artifacts']))
        for i in (0, 1, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Filter with invalid operator leads to BadRequest
        filters = [('dict_of_str', 'invalid:a')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Return artifacts that contain key one in 'dict_of_int'
        filters = [('dict_of_int', 'eq:one')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain key one or three in 'dict_of_int'
        filters = [('dict_of_int', 'in:one,three')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(4, len(res['artifacts']))
        for i in (0, 1, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Filter by dicts values
        # Return artifacts that contain value 'bb' in 'dict_of_str[b]'
        filters = [('dict_of_str.b', 'eq:bb')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 1, 4):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain values 'aa' or 'bb' in 'dict_of_str[a]'
        filters = [('dict_of_str.a', 'in:aa,bb')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Filter with invalid operator leads to BadRequest
        filters = [('dict_of_str.a', 'invalid:aa')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Return artifacts that contain value '2' in 'dict_of_int[two]'
        filters = [('dict_of_int.two', 'eq:2')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 1, 4):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain values '1' or '2' in 'dict_of_int[one]'
        filters = [('dict_of_int.one', 'in:1,2')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Filter with invalid operator leads to BadRequest
        filters = [('dict_of_int.one', 'invalid:1')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Return artifacts that contain key 'aa' in 'list_of_str'
        filters = [('list_of_str', 'eq:aa')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain key 'aa' or 'cc' in 'list_of_str'
        filters = [('list_of_str', 'in:aa,cc')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(4, len(res['artifacts']))
        for i in (0, 1, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Filter with invalid operator leads to BadRequest
        filters = [('list_of_str', 'invalid:aa')]
        self.assertRaises(exc.BadRequest, self.controller.list,
                          self.req, 'sample_artifact', filters)

        # Return artifacts that contain key 1 in 'list_of_int'
        filters = [('list_of_int', 'eq:1')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(3, len(res['artifacts']))
        for i in (0, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

        # Return artifacts that contain key 1 or three in 'list_of_int'
        filters = [('list_of_int', 'in:1,3')]
        res = self.controller.list(self.req, 'sample_artifact', filters)
        self.assertEqual(4, len(res['artifacts']))
        for i in (0, 1, 2, 3):
            self.assertIn(arts[i], res['artifacts'])

    def test_list_and_sort_fields(self):
        # Create a bunch of artifacts for list sorting tests
        values = [
            {'name': 'art0', 'float1': 0.00, 'float2': 2.0, 'int1': 0, 'int2':
                0, 'str1': "string0", 'version': 0.0, },
            {'name': 'art1', 'float1': 0.01, 'float2': 2.1, 'int1': 1, 'int2':
                11, 'str1': "string1", 'version': 0.1, },
            {'name': 'art2', 'float1': 0.02, 'float2': 2.2, 'int1': 2, 'int2':
                22, 'str1': "string2", 'version': 0.2, },
            {'name': 'art3', 'float1': 0.03, 'float2': 2.3, 'int1': 3, 'int2':
                33, 'str1': "string3", 'version': 0.3, },
            {'name': 'art4', 'float1': 0.04, 'float2': 2.4, 'int1': 4, 'int2':
                44, 'str1': "string4", 'version': 0.4, },
            {'name': 'art5', 'float1': 0.05, 'float2': 2.5, 'int1': 5, 'int2':
                55, 'str1': "string5", 'version': 0.5, },
            {'name': 'art6', 'float1': 0.06, 'float2': 2.6, 'int1': 6, 'int2':
                66, 'str1': "string6", 'version': 0.6, },
        ]

        arts = [self.controller.create(self.req, 'sample_artifact', val)
                for val in values]

        # sort by name:
        arts_sort_name_asc = self.controller.list(self.req, 'sample_artifact',
                                                  [], sort=[("name", "asc")])
        self.assertEqual(7, len(arts_sort_name_asc['artifacts']))
        self.assertEqual(arts_sort_name_asc['artifacts'][0]['name'],
                         arts[0]['name'])
        self.assertEqual(arts_sort_name_asc['artifacts'][6]['name'],
                         arts[6]['name'])

        arts_sort_name_desc = self.controller.list(self.req, 'sample_artifact',
                                                   [], sort=[("name", "desc")])
        self.assertEqual(7, len(arts_sort_name_desc['artifacts']))
        self.assertEqual(arts_sort_name_desc['artifacts'][0]['name'],
                         arts[6]['name'])
        self.assertEqual(arts_sort_name_desc['artifacts'][6]['name'],
                         arts[0]['name'])

        # sort by float1
        arts_sort_float1_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("float1", "asc")])
        self.assertEqual(7, len(arts_sort_float1_asc['artifacts']))
        self.assertEqual(arts_sort_float1_asc['artifacts'][0]['float1'],
                         arts[0]['float1'])
        self.assertEqual(arts_sort_float1_asc['artifacts'][6]['float1'],
                         arts[6]['float1'])

        arts_sort_float1_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("float1", "desc")])
        self.assertEqual(7, len(arts_sort_float1_desc['artifacts']))
        self.assertEqual(arts_sort_float1_desc['artifacts'][0]['float1'],
                         arts[6]['float1'])
        self.assertEqual(arts_sort_float1_desc['artifacts'][6]['float1'],
                         arts[0]['float1'])
        # arts_sort_float2 = self.controller.list(self.req, 'sample_artifact',
        # [], sort=[("float2", "asc")])

        # sort by int1
        arts_sort_int1_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("float1", "asc")])
        self.assertEqual(7, len(arts_sort_int1_asc['artifacts']))
        self.assertEqual(arts_sort_int1_asc['artifacts'][0]['int1'],
                         arts[0]['int1'])
        self.assertEqual(arts_sort_int1_asc['artifacts'][6]['int1'],
                         arts[6]['int1'])

        arts_sort_int1_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("float1", "desc")])
        self.assertEqual(7, len(arts_sort_int1_desc['artifacts']))
        self.assertEqual(arts_sort_int1_desc['artifacts'][0]['int1'],
                         arts[6]['int1'])
        self.assertEqual(arts_sort_int1_desc['artifacts'][6]['int1'],
                         arts[0]['int1'])
        # arts_sort_int2= self.controller.list(self.req, 'sample_artifact'
        # , [], sort=[("int2", "asc")])

        # Todo: sort by id
        # arts_sort_id_asc = self.controller.list(self.req, 'sample_artifact',
        #  [], sort=[("id", "asc")])
        # self.assertEqual(7, len(arts_sort_name_asc['artifacts']))
        # self.assertEqual(arts_sort_int1_asc['artifacts'][0]['id'],
        #  arts[0]['id'])
        # self.assertEqual(arts_sort_int1_asc['artifacts'][6]['id'],
        #  arts[6]['id'])
        #
        # arts_sort_id_desc = self.controller.list(self.req,
        # 'sample_artifact', [], sort=[("id", "desc")])
        # self.assertEqual(7, len(arts_sort_id_desc['artifacts']))
        # self.assertEqual(arts_sort_id_desc['artifacts'][0]['id'],
        #  arts[6]['id'])
        # self.assertEqual(arts_sort_id_desc['artifacts'][6]['id'],
        #  arts[0]['id'])

        # sort by created_at
        arts_sort_created_at_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("created_at", "asc")])
        self.assertEqual(7, len(arts_sort_created_at_asc['artifacts']))
        self.assertEqual(arts_sort_created_at_asc['artifacts'][0]
                         ['created_at'], arts[0]['created_at'])
        self.assertEqual(arts_sort_created_at_asc['artifacts'][6]
                         ['created_at'], arts[6]['created_at'])

        arts_sort_created_at_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("created_at", "desc")])
        self.assertEqual(7, len(arts_sort_created_at_desc['artifacts']))
        self.assertEqual(arts_sort_created_at_desc['artifacts'][0]
                         ['created_at'], arts[6]['created_at'])
        self.assertEqual(arts_sort_created_at_desc['artifacts'][6]
                         ['created_at'], arts[0]['created_at'])
        # sort by str1
        arts_sort_str1_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("str1", "asc")])
        self.assertEqual(7, len(arts_sort_str1_asc['artifacts']))
        self.assertEqual(arts_sort_str1_asc['artifacts'][0]['str1'],
                         arts[0]['str1'])
        self.assertEqual(arts_sort_str1_asc['artifacts'][6]['str1'],
                         arts[6]['str1'])

        arts_sort_str1_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("str1", "desc")])
        self.assertEqual(7, len(arts_sort_str1_desc['artifacts']))
        self.assertEqual(arts_sort_str1_desc['artifacts'][0]['str1'],
                         arts[6]['str1'])
        self.assertEqual(arts_sort_str1_desc['artifacts'][6]['str1'],
                         arts[0]['str1'])

        # sort by system_attribute
        arts_sort_system_attribute_asc = self.controller.list(
            self.req, 'sample_artifact', [],
            sort=[("system_attribute", "asc")])
        self.assertEqual(7, len(arts_sort_system_attribute_asc['artifacts']))
        self.assertEqual(arts_sort_system_attribute_asc['artifacts'][0]
                         ['system_attribute'], arts[0]['system_attribute'])
        self.assertEqual(arts_sort_system_attribute_asc['artifacts'][6]
                         ['system_attribute'], arts[6]['system_attribute'])

        arts_sort_system_attribute_desc = self.controller.list(
            self.req, 'sample_artifact', [],
            sort=[("system_attribute", "desc")])
        self.assertEqual(7, len(arts_sort_system_attribute_desc['artifacts']))
        self.assertEqual(arts_sort_system_attribute_desc['artifacts'][0]
                         ['system_attribute'], arts[6]['system_attribute'])
        self.assertEqual(arts_sort_system_attribute_desc['artifacts'][6]
                         ['system_attribute'], arts[0]['system_attribute'])

        # sort by updated_at
        arts_sort_updated_at_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("updated_at", "asc")])
        self.assertEqual(7, len(arts_sort_updated_at_asc['artifacts']))
        self.assertEqual(arts_sort_updated_at_asc['artifacts'][0]
                         ['updated_at'], arts[0]['updated_at'])
        self.assertEqual(arts_sort_updated_at_asc['artifacts'][6]
                         ['updated_at'], arts[6]['updated_at'])

        arts_sort_updated_at_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("updated_at", "desc")])
        self.assertEqual(7, len(arts_sort_updated_at_desc['artifacts']))
        self.assertEqual(arts_sort_updated_at_desc['artifacts'][0]
                         ['updated_at'], arts[0]['updated_at'])
        self.assertEqual(arts_sort_updated_at_desc['artifacts'][6]
                         ['updated_at'], arts[6]['updated_at'])

        # sort by visibility
        arts_sort_visibility_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("visibility", "asc")])
        self.assertEqual(7, len(arts_sort_visibility_asc['artifacts']))
        self.assertEqual(arts_sort_visibility_asc['artifacts'][0]
                         ['visibility'], arts[0]['visibility'])
        self.assertEqual(arts_sort_visibility_asc['artifacts'][6]
                         ['visibility'], arts[6]['visibility'])

        arts_sort_visibility_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("visibility", "desc")])
        self.assertEqual(7, len(arts_sort_visibility_desc['artifacts']))
        self.assertEqual(arts_sort_visibility_desc['artifacts'][0]
                         ['visibility'], arts[0]['visibility'])
        self.assertEqual(arts_sort_visibility_desc['artifacts'][6]
                         ['visibility'], arts[6]['visibility'])

        # sort by version
        arts_sort_version_asc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("version", "asc")])
        self.assertEqual(7, len(arts_sort_version_asc['artifacts']))
        self.assertEqual(arts_sort_version_asc['artifacts'][0]['version'],
                         arts[0]['version'])
        self.assertEqual(arts_sort_version_asc['artifacts'][6]['version'],
                         arts[6]['version'])

        arts_sort_version_desc = self.controller.list(
            self.req, 'sample_artifact', [], sort=[("version", "desc")])
        self.assertEqual(7, len(arts_sort_version_desc['artifacts']))
        self.assertEqual(arts_sort_version_desc['artifacts'][0]['version'],
                         arts[6]['version'])
        self.assertEqual(arts_sort_version_desc['artifacts'][6]['version'],
                         arts[0]['version'])
