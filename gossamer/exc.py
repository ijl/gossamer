"""
Exceptions
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

class TestError(RuntimeError):
    """
    Generic.
    """

class NoScreenshotsRecorded(Exception):
    """
    A test is recorded with no screenshots made.
    """

class RecordedRunEmpty(Exception):
    """
    A record.json file is empty, meaning a run didn't complete.
    """

class CouldNotParseRecordedRun(Exception):
    """
    Couldn't read a record.json for some reason.
    """

class RecordedRunDoesNotExist(Exception):
    """
    A record.json file does not exist.
    """
class UnknownTestName(Exception):
    """
    Test name given via CLI is not known from a file.
    """

class DoNotOverwrite(Exception):
    """
    User indicates they don't want to overwrite an existing test.
    """

class EmptyPath(Exception):
    """
    In playing back, a data directory did not exist.
    """

class DifferentBrowser(Exception):
    """
    The recorded browser is different than the user-supplied browser.
    """

class InvalidBrowser(Exception):
    """
    We don't recognize a given `browser` value.
    """

class InvalidGossamerfile(Exception):
    """
    An error parsing the Gossamerfile.
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

class ElementNotVisible(Exception):
    """
    WebDriver reports element not visible... not enough delay when something
    was being hidden/unhidden or rendered.
    """

class UnavailableBrowser(Exception):
    """
    WebDriver isn't starting with the user's browser selected.
    """

class WebDriverConnectionFailed(Exception):
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
