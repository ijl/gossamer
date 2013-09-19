"""
Integrate with unittest.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest
import subprocess

from gossamer.main import dispatch
from gossamer.constant import modes, states, LOCAL_WEBDRIVER_URL, REMOTE_WEBDRIVER_URL, \
    DEFAULT_BROWSER
from gossamer import util, exc


def run_gossamerfile(
        gossamerfile, data_dir,
        browser=None, local=None, remote=None,
        start_webdriver=None, webdriver_path=None
    ): # pylint: disable=R0913
    """
    Call this to read a Gossamerfile and run all of its tests.
    """
    case = GossamerTestCase
    if start_webdriver is True:
        if not webdriver_path or not isinstance(webdriver_path, (str, unicode)):
            raise ValueError(
                'Must specify `webdriver_path`, as absolute path to the '
                'Selenium WebDriver JAR.'
            )
        case.start_webdriver = start_webdriver
        case.webdriver_path = webdriver_path

    browser = browser or DEFAULT_BROWSER
    local = local or LOCAL_WEBDRIVER_URL
    remote = remote or REMOTE_WEBDRIVER_URL

    options = {'browser': browser, 'local': local, 'remote': remote}

    tests = util.make_tests([gossamerfile], modes.PLAYBACK, data_dir, **options)
    for key, test in tests.items():
        setattr(case, 'test_%s' % key,
            _nose_wrapper(case, key, test, test.settings.browser, local, remote)
        )
    return case


def _nose_wrapper(*args): # pylint: disable=W0613
    """
    Creates GossamerTestCase methods that will themselves run the tests.
    """
    return lambda args: _run_nose(*args)


def _run_nose(self, name, test, browser, local, remote): # pylint: disable=R0913
    """
    Run a test for Nose.
    """
    try:
        driver = util.get_driver(browser, local, remote)
        result = dispatch(driver, modes.PLAYBACK, {name: test, })[name]
        if result == states.FAIL:
            self.fail()
        elif result == states.ERROR:
            raise exc.TestError() # todo
    finally:
        driver.quit()


class GossamerTestCase(unittest.TestCase): # pylint: disable=R0904
    """
    unittest case.

    By specifying start_webdriver as bool and webdriver_path as absolute path
    to the WebDriver JAR, one can have the webdriver automatically started.
    Is this a good idea? I don't know.
    """

    start_webdriver = False
    webdriver_path = None
    webdriver = None

    def setUp(self):
        super(GossamerTestCase, self).setUp()
        if self.start_webdriver:
            if not self.webdriver_path or not isinstance(self.webdriver_path, (str, unicode)):
                raise ValueError(
                    'Must specify `webdriver_path`, as absolute path to the '
                    'Selenium WebDriver JAR.'
                )
            self.webdriver = subprocess.Popen(
                ['java -jar %s' % self.webdriver_path], stdout=subprocess.PIPE
            )

    def tearDown(self):
        if self.webdriver:
            self.webdriver.terminate() # pylint: disable=E1101
        super(GossamerTestCase, self).tearDown()

