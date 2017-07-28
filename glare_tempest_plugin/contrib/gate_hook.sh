#!/usr/bin/env bash
# Copyright 2017 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

echo "gate_hook.sh executed"

export DEVSTACK_GATE_TEMPEST=1
export KEEP_LOCALRC=1

GATE_DEST=$BASE/new
DEVSTACK_PATH=$GATE_DEST/devstack
$GATE_DEST/devstack-gate/devstack-vm-gate.sh