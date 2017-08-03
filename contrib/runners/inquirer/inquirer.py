# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uuid

from st2common import log as logging
from st2common.constants.action import LIVEACTION_STATUS_SUCCEEDED
from st2common.constants.action import LIVEACTION_STATUS_FAILED
from st2common.constants.action import LIVEACTION_STATUS_PENDING
from st2common.runners.base import ActionRunner
from st2common.runners import python_action_wrapper
from st2common.services import action as action_service
from st2common.util import action_db as action_utils


LOG = logging.getLogger(__name__)

__all__ = [
    'get_runner',
    'Inquirer',
]

# constants to lookup in runner_parameters.
RUNNER_SCHEMA = 'schema'
RUNNER_ROLES = 'roles'
RUNNER_USERS = 'users'
RUNNER_TAG = 'tag'

#TODO
BASE_DIR = os.path.dirname(os.path.abspath(python_action_wrapper.__file__))


def get_runner():
    'RunnerTestCase',
    return Inquirer(str(uuid.uuid4()))


class Inquirer(ActionRunner):
    """This runner implements the ability to ask for more input during a workflow
    """

    def __init__(self, runner_id):
        super(Inquirer, self).__init__(runner_id=runner_id)

    def pre_run(self):
        super(Inquirer, self).pre_run()

        # TODO :This is awful, but the way "runner_parameters" and other variables get
        # assigned on the runner instance is even worse. Those arguments should
        # be passed to the constructor.
        self.schema = self.runner_parameters.get(RUNNER_SCHEMA, None)
        self.roles_param = self.runner_parameters.get(RUNNER_ROLES, None)
        self.users_param = self.runner_parameters.get(RUNNER_USERS, None)

    def run(self, action_parameters):

        # Retrieve existing result (initialize if needed)
        liveaction_db = action_utils.get_liveaction_by_id(self.liveaction_id)
        response_data = liveaction_db.result.get("response_data")
        if not response_data:
            response_data = {"response": {}}

        # Request pause of parent execution
        if liveaction_db.parent:
            # TODO get current user
            action_service.request_pause(self.liveaction_id, "st2admin")
        else:
            LOG.error("Inquiries must be run within a workflow.")
            return (LIVEACTION_STATUS_FAILED, response_data, None)

        # Validate repsonse and return
        if action_service.validate_response(self.schema, response_data):
            return (LIVEACTION_STATUS_SUCCEEDED, response_data, None)
        else:

            # TODO raise trigger
            return (LIVEACTION_STATUS_PENDING, response_data, None)
