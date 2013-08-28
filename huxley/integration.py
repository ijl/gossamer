# Copyright (c) 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Integrate with unittest.
"""

import os
import unittest
import sys

from huxley.main import dispatch
from huxley.consts import modes, LOCAL_WEBDRIVER_URL, REMOTE_WEBDRIVER_URL, \
    DEFAULT_BROWSER
from huxley import util

# Python unittest integration. These fail when the screen shots change, and they
# will pass the next time since they write new ones.
class HuxleyTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case... why not use setUp and tearDown? multiple huxley files?
    """
    mode = None
    local_webdriver_url = LOCAL_WEBDRIVER_URL
    remote_webdriver_url = REMOTE_WEBDRIVER_URL

    def setUp(self):
        super(HuxleyTestCase, self).setup(self)

    def huxley(self, filename, url, postdata=None):
        msg = 'Running Huxley test: ' + os.path.basename(filename)
        print
        print '-' * len(msg)
        print msg
        print '-' * len(msg)

        browser = DEFAULT_BROWSER # todo
        cwd = os.getcwd() # os.abspath(filename)?

        # TODO data_dir
        
        try:
            driver = util.get_driver(browser)
            tests = util.make_tests(filename, self.mode, cwd, data_dir,
                postdata=postdata
            )
            logs = dispatch(driver, self.mode, tests)

            # self.assertEqual(0, r, 
            #     'New screenshots were taken and written. '
            #     'Please be sure to review and check in.')
        finally:
            driver.quit()

    def tearDown(self):
        pass


def unittest_main(module='__main__'):
    """
    unittest integration... TODO
    """
    if len(sys.argv) > 1 and sys.argv[1] == 'record':
        # Create a new test by recording the user's browsing session
        HuxleyTestCase.mode = modes.RECORD
    elif len(sys.argv) > 1 and sys.argv[1] == 'playback':
        # When running in a continuous test runner you may want the
        # tests to continue to fail (rather than re-recording new screen
        # shots) to indicate a commit that changed a screen shot but did
        # not rerecord. TODO: we may want to build in auto-retry functionality
        # and automatically back off the sleep factor.
        HuxleyTestCase.mode = modes.PLAYBACK
    # The default behavior is to play back the test and save new screen shots
    # if they change.

    unittest.main(module)
