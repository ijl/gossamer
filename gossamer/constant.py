"""
Application constants including run modes and exit codes.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import os
import json


DEFAULT_TESTFILE = 'Gossamerfile'

DEFAULT_WEBDRIVER = 'http://localhost:4444/wd/hub'

LOCAL_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', DEFAULT_WEBDRIVER)
REMOTE_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', DEFAULT_WEBDRIVER)
ENV_DEFAULTS = json.loads(os.environ.get('HUXLEY_DEFAULTS', 'null'))

DEFAULT_DIFFCOLOR = '0,255,0'
DEFAULT_SCREENSIZE = '1024x768'
DEFAULT_BROWSER = 'firefox'

DATA_VERSION = 1

class _TestRunModes(object): # pylint: disable=R0903
    """
    Indicates what a given test run should be doing, e.g., recording.
    """
    RECORD = 1
    RERECORD = 2
    PLAYBACK = 3


class _ExitCodes(object): # pylint: disable=R0903
    """
    Exit codes...
    """
    OK = 0
    FAILED = 1
    ERROR = 2
    ARGUMENT_ERROR = 3 # CLI interface
    RECORDED_RUN_ERROR = 4 # Something went wrong with loading recorded records

class _OK(object): # pylint: disable=R0903,C0111
    def __unicode__(self): # pragma: no cover, pylint: disable=R0201
        return u'ok'
    def __str__(self): # pragma: no cover
        return self.__unicode__()

class _FAIL(object): # pylint: disable=R0903,C0111
    def __unicode__(self): # pragma: no cover, pylint: disable=R0201
        return u'FAIL'
    def __str__(self): # pragma: no cover
        return self.__unicode__()

class _ERROR(object): # pylint: disable=R0903,C0111
    def __unicode__(self): # pragma: no cover, pylint: disable=R0201
        return u'ERROR'
    def __str__(self): # pragma: no cover
        return self.__unicode__()

class _StatusCodes(object): # pylint: disable=R0903
    """
    Status codes, namely OK/FAIL/ERROR.
    """
    OK = _OK()
    FAIL = _FAIL()
    ERROR = _ERROR()


modes = _TestRunModes()
exits = _ExitCodes()
states = _StatusCodes()
