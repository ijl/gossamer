"""
Integrate with unittest.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest

from gossamer.main import dispatch
from gossamer.constant import modes, states, LOCAL_WEBDRIVER_URL
from gossamer import util, exc


def run_gossamerfile(
        client_locals, gossamerfile, data_dir,
        selenium=None, skip_allowed=True
    ): # pylint: disable=R0913
    """
    Call this to read a Gossamerfile and run all of its tests.
    """
    if isinstance(gossamerfile, (str, unicode)):
        gossamerfile = [gossamerfile]

    selenium = selenium or LOCAL_WEBDRIVER_URL
    options = {'local': selenium, 'remote': selenium}

    driver_ok = util.check_driver(selenium)

    tests = util.make_tests(gossamerfile, modes.PLAYBACK, data_dir, **options)
    for key, test in tests.items():
        case = type(
            'GossamerTestCase',
            GossamerTestCase.__bases__,
            dict(GossamerTestCase.__dict__)
        )
        case._skip_allowed = skip_allowed # pylint: disable=W0212
        case._driver_ok = driver_ok # pylint: disable=W0212
        case.runTest = _nose_wrapper(
            case, key, test, test.settings.browser, selenium, selenium
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
        log = dispatch(
            driver, modes.PLAYBACK, {name: test, }, output=util.null_writer
        )
        result, err = [each[name] for each in log]
        if result == states.FAIL:
            self.fail()
        elif result == states.ERROR:
            if err is not None:
                raise err
            raise exc.TestError() # todo
    finally:
        util.close_driver(driver)


class GossamerTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case.
    """

    _skip_allowed = True
    _driver_ok = True

    def setUp(self):
        super(GossamerTestCase, GossamerTestCase()).setUp()
        if not self._driver_ok:
            if self._skip_allowed:
                self.skipTest("Selenium Server is not available")
            else:
                raise exc.WebDriverConnectionFailed(
                    "Selenium Server is not available"
                )

    def runTest(self):
        """
        Replaced within :func:`run_gossamerfile`.
        """
        pass
