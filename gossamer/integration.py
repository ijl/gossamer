"""
Integrate with unittest.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest

from gossamer.main import dispatch
from gossamer.constant import modes, states, DEFAULT_WEBDRIVER
from gossamer import util, exc


def run_gossamerfile(
        client_locals, gossamerfile, data_dir,
        selenium=None, skip_allowed=True, rewrite_url=None
    ): # pylint: disable=R0913
    """
    Call this to read one or more Gossamerfiles and run all of their tests.
    It will mutate the locals() passed to it by the inclusion of a complete
    `unittest.TestCase` for every test in the given Gossamerfiles. Test
    runners will then automatically add your tests.

    Parameters:

        client_locals, locals() dictionary:
            `locals()` of the module from which the func is being called.

        gossamerfile, {str, list, tuple, dict}:
            Location to one or more Gossamerfiles.

        data_dir:
            The data directory containing the recorded tests and screenshots.

        selenium (optional), str:
            If provided, the Selenium Server URL to use instead of that in
            the recorded tests. Use this to change servers with environments.

        skip_allowed (optional), bool:
            If true, if Selenium Server is not running,
            unittest will skip this test; if false, it will error. Default
            true.

        rewrite_url (optional), callable:
            If given, test URLs will be rewritten according to the provided
            callable. This callable should accept a single parameter, a string,
            which is the URL in the recorded test. Use this to change the
            environment used. E.g., lambda x: x.replace('http://dev.', 'http://ci.').

    """
    if isinstance(gossamerfile, (str, unicode)):
        gossamerfile = [gossamerfile]
    elif isinstance(gossamerfile, dict):
        gossamerfile = [val for _, val in gossamerfile.items()]

    selenium = selenium or DEFAULT_WEBDRIVER

    driver_ok = util.check_driver(selenium)

    tests = util.make_tests(
        gossamerfile, modes.PLAYBACK, data_dir, rewrite_url=rewrite_url
    )
    for key, test in tests.items():
        case = type(
            'GossamerTestCase',
            GossamerTestCase.__bases__,
            dict(GossamerTestCase.__dict__)
        )
        case._skip_allowed = skip_allowed # pylint: disable=W0212
        case._driver_ok = driver_ok # pylint: disable=W0212
        case._args = (test, test.settings.browser, selenium)
        case._gossamer_test = test # pylint: disable=W0212
        case.runTest.__func__.__doc__ = test.settings.desc or test.settings.name # pylint: disable=E1101,C0301
        client_locals['GossamerTest_%s' % key] = case
    return True


class GossamerTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case.
    """

    _skip_allowed = True
    _driver_ok = True
    _gossamer_test = None
    _args = ()

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
        Gossamer test
        """
        test, browser, selenium = self._args
        try:
            driver = util.get_driver(browser, selenium)
            result, err = dispatch(
                driver, modes.PLAYBACK,  test, output=util.null_writer
            )
            if result == states.FAIL:
                if err is not None:
                    self.fail(str(err))
                else:
                    self.fail('Screenshots were different.')
            elif result == states.ERROR:
                if err is not None:
                    raise err
                raise exc.TestError() # todo
        finally:
            util.close_driver(driver)
