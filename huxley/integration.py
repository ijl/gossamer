"""
Integrate with unittest.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import os
import unittest
# import sys

from huxley.main import dispatch
from huxley.constant import modes, LOCAL_WEBDRIVER_URL, REMOTE_WEBDRIVER_URL, \
    DEFAULT_BROWSER
from huxley import util

def run_huxleyfile(huxleyfile, data_dir, browser=None, local=None, remote=None):
    """
    Call this to read a Huxleyfile and run all of its tests.
    """
    case = HuxleyTestCase

    cwd = os.getcwd()

    browser = browser or DEFAULT_BROWSER
    local = local or LOCAL_WEBDRIVER_URL
    remote = remote or REMOTE_WEBDRIVER_URL

    options = {'browser': browser, 'local': local, 'remote': remote}

    tests = util.make_tests([huxleyfile], case.mode, cwd, data_dir, **options)
    try:
        case.driver = util.get_driver(browser, local, remote)
        for key, test in tests.items():
            case.tests.append(dispatch(case.driver, case.mode, {key: test, }))
        return case
    finally:
        case.driver.quit() # eeek. why wasn't tearDown doing it?

class HuxleyTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case.
    """
    mode = modes.PLAYBACK
    tests = []


# def unittest_main(module='__main__'):
#     """
#     unittest integration.

#     When running in a continuous test runner you may want the
#     tests to continue to fail (rather than re-recording new screen
#     shots) to indicate a commit that changed a screen shot but did
#     not rerecord.
#     and automatically back off the sleep factor.

#     The default behavior is to play back the test and save new screen shots
#     if they change.
#     """
#     # sys.argv[0] is Huxleyfile
#     HuxleyTestCase.huxleyfile = sys.argv[0]
#     unittest.main(module)
