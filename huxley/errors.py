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
Exceptions
"""

class TestError(RuntimeError):
    """
    TODO: replace
    """
    pass

class NoScreenshotsRecorded(Exception):
    """
    A test is recorded with no screenshots made.
    """
    pass

class RecordedRunEmpty(Exception):
    """
    A record.json file is empty, meaning a run didn't complete.
    """

class RecordedRunDoesNotExist(Exception):
    """
    A record.json file does not exist.
    """

class DoNotOverwrite(Exception):
    """
    User indicates they don't want to overwrite an existing test.
    """

class InvalidBrowser(Exception):
    """
    We don't recognize a given `browser` value.
    """

class InvalidHuxleyfile(Exception):
    """
    An error parsing the Huxleyfile.
    """

class InvalidWebDriverConfiguration(Exception):
    """
    WebDriver throws an exception while setting up.
    """

class ImageNotFound(Exception):
    """
    Imagediff was passed a filename to an image that doesn't exist.
    """

class PlaybackTimeout(Exception):
    """
    We waited for the page to be unchanging (via watching mutations), 
    and the wait exceeded our timeout.
    """

class WebDriverRefusedConnection(Exception):
    """
    Cannot connect to the webdriver--is it running?
    """

class WebDriverWentAway(Exception):
    """
    WebDriver raises an inability to communicate with the user agent.
    """

class WebDriverSecurityError(Exception):
    """
    WebDriver gave a security error.
    """
