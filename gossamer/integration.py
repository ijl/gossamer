"""
Integrate with unittest.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest

from gossamer.main import dispatch
from gossamer.constant import modes, states, LOCAL_WEBDRIVER_URL, REMOTE_WEBDRIVER_URL
from gossamer import util, exc


def run_gossamerfile(
        client_locals, gossamerfile, data_dir,
        browser=None, local=None, remote=None
    ): # pylint: disable=R0913
    """
    Call this to read a Gossamerfile and run all of its tests.
    """
    if isinstance(gossamerfile, (str, unicode)):
        gossamerfile = [gossamerfile]

    local = local or LOCAL_WEBDRIVER_URL
    remote = remote or REMOTE_WEBDRIVER_URL

    options = {'browser': browser, 'local': local, 'remote': remote}

    tests = util.make_tests(gossamerfile, modes.PLAYBACK, data_dir, **options)

    for key, test in tests.items():
        case = GossamerTestCase
        setattr(
            case,
            'runTest',
            _nose_wrapper(case, key, test, test.settings.browser, local, remote)
        )
        case.runTest.__func__.__doc__ = test.settings.desc or test.settings.name # pylint: disable=E1101,C0301
        client_locals['GossamerTest_%s' % key] = case
    return True


def _nose_wrapper(self, *args): # pylint: disable=W0613
    """
    Creates GossamerTestCase methods that will themselves run the tests.
    """
    return lambda x: _run_nose(x, *args)


def _run_nose(self, name, test, browser, local, remote): # pylint: disable=R0913
    """
    Run a test for Nose.
    """
    try:
        driver = util.get_driver(browser, local, remote)
        result = dispatch(
            driver, modes.PLAYBACK, {name: test, }, output=util.null_writer
        )[name]
        if result == states.FAIL:
            self.fail()
        elif result == states.ERROR:
            raise exc.TestError() # todo
    finally:
        util.close_driver(driver)


class GossamerTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case.
    """
