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
Application constants including run modes and exit codes.
"""

import os
import json

DEFAULT_TESTFILE = 'Huxleyfile'

DEFAULT_WEBDRIVER = 'http://localhost:4444/wd/hub'

LOCAL_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', DEFAULT_WEBDRIVER)
REMOTE_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', DEFAULT_WEBDRIVER)
ENV_DEFAULTS = json.loads(os.environ.get('HUXLEY_DEFAULTS', 'null'))

DEFAULT_DIFFCOLOR = '0,255,0'
DEFAULT_SCREENSIZE = '1024x768'
DEFAULT_BROWSER = 'firefox'


DEFAULTS = {
    'screensize': DEFAULT_SCREENSIZE,
    # etc.
}

class _TestRunModes(object): # pylint: disable=R0903
    """
    Indicates what a given test run should be doing, e.g., recording.
    """
    RECORD = 1
    RERECORD = 2
    PLAYBACK = 3

modes = _TestRunModes()

class _ExitCodes(object): # pylint: disable=R0903
    """
    Exit codes... 1 doesn't make sense to me as it's a desired exit, todo...
    """
    OK = 0
    NEW_SCREENSHOTS = 1
    ERROR = 2
    ARGUMENT_ERROR = 3 # CLI interface
    RECORDED_RUN_ERROR = 4 # Something went wrong with loading recorded records

exits = _ExitCodes()