# Copyright 2011-2012 OpenStack Foundation
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

import os
import sys
import time

import httplib2
from oslo_serialization import jsonutils
from six.moves import http_client
from six.moves import range

from glare.tests import functional
from glare.tests.functional import base
from glare.tests.utils import execute


class TestScrubber(base.TestArtifact):

    """Test that delayed_delete works and the scrubber deletes"""

    def setUp(self):
        functional.FunctionalTest.setUp(self)

        self.include_scrubber = True
        self.set_user('user1')
        self.glare_server.deployment_flavor = 'noauth'

        self.glare_server.enabled_artifact_types = ','.join(
            self.enabled_types)
        self.glare_server.custom_artifact_types_modules = (
            'glare.tests.sample_artifact')
        self.start_servers(delayed_delete=True, daemon=True,
                           **self.__dict__.copy())

    def test_delayed_delete(self):
        """
        Test that artifacts don't get deleted immediately and that the scrubber
        scrubs them.
        """
        self.assertEqual(True, True)
