"""
Utilities.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import os
import sys
import json
import jsonpickle # pylint: disable=F0401
import ConfigParser
from selenium.common.exceptions import WebDriverException # pylint: disable=F0401
from urllib2 import URLError

from selenium import webdriver  # pylint: disable=F0401

from huxley import exc

from huxley.constant import modes, exits, \
    DEFAULT_DIFFCOLOR, REMOTE_WEBDRIVER_URL

def logger(name, level=None):
    """
    Create logger with appropriate level.
    """
    import logging
    ret = logging.getLogger(name)
    ret.addHandler(logging.StreamHandler())
    ret.setLevel(getattr(logging, level) if level else logging.INFO)
    return ret

# level can be overriden to DEBUG in CLI with -v
log = logger(__name__, 'INFO')

DRIVERS = {
    'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
    'ie': webdriver.Ie,
    'opera': webdriver.Opera
}

CAPABILITIES = {
    'firefox': webdriver.DesiredCapabilities.FIREFOX,
    'chrome': webdriver.DesiredCapabilities.CHROME,
    'ie': webdriver.DesiredCapabilities.INTERNETEXPLORER,
    'opera': webdriver.DesiredCapabilities.OPERA
}

def read_recorded_run(filename):
    """
    Load a serialized run.
    """
    try:
        if os.path.getsize(filename) <= 0:
            raise exc.RecordedRunEmpty('%s is empty' % filename)
    except OSError:
        raise exc.RecordedRunDoesNotExist('%s does not exist' % filename)
    try:
        with open(filename, 'r') as fp:
            recorded_run = jsonpickle.decode(fp.read())
        if recorded_run.version != 1:
            raise NotImplementedError()
        return recorded_run
    except ValueError: # couldn't parse
        raise exc.CouldNotParseRecordedRun('Could not parse %s' % filename)


def write_recorded_run(filename, output):
    """
    Serialize a recorded run to a JSON file.
    """
    try:
        with open(os.path.join(filename, 'record.json'), 'w') as fp:
            fp.write(
                jsonpickle.encode(
                    output
                )
            ) # todo version the recorded run, and validate it
    except Exception as exception: # todo how can this fail
        raise exception
    return True



def get_driver(browser, local_webdriver=None, remote_webdriver=None):
    """
    Get a webdriver. The caller is responsible for closing the driver.

    Browser is required. Local and remote are optional, with remote
    taking precedence.
    """
    if local_webdriver and not remote_webdriver:
        driver_url = local_webdriver
    else:
        driver_url = remote_webdriver or REMOTE_WEBDRIVER_URL
    try:
        driver = webdriver.Remote(driver_url, CAPABILITIES[browser])
    except KeyError:
        raise exc.InvalidBrowser(
            'Invalid browser %r; valid browsers are %r.' % (browser, DRIVERS.keys())
        )
    except URLError as exception:
        raise exc.WebDriverRefusedConnection(
            'We cannot connect to the WebDriver %s -- is it running?' % driver_url
        )
    except WebDriverException as exception:
        if exception.msg.startswith('The path to the driver executable must be set'):
            raise exc.InvalidWebDriverConfiguration(
                'WebDriver cannot locate the driver for %s: %s' % (browser, exception.msg)
            )
        raise
    return driver


def prompt(display, options=None, testname=None):
    """
    Given text as `display` and optionally `options` as an
    iterable containing acceptable input, returns a boolean
    of whether the prompt was met.
    """
    sys.stdout.write(display)
    sys.stdout.write('\n')
    sys.stdout.flush()
    inp = raw_input('huxley%s >>> ' % (':'+testname if testname else ''))
    if options:
        if inp in options:
            return True
        return False
    return True


def _postdata(arg):
    """
    Given CLI input `arg`, resolve postdata.
    """
    if arg:
        if arg == '-':
            return sys.stdin.read()
        else:
            with open(arg, 'r') as f:
                data = json.loads(f.read())
            return data
    return None


def verify_and_prepare_files(filename, testname, mode, overwrite):
    """
    Prepare directories on file system, including clearing existing data
    if necessary.
    """
    log.debug(filename)
    if os.path.exists(filename):
        if mode == modes.RECORD: # todo weirdness with rerecord
            if os.path.getsize(filename) > 0:
                if not overwrite and not prompt(
                    '\n%s already exists--clear existing '
                    'screenshots and overwrite test? [Y/n] ' \
                        % testname,
                    ('Y', 'y')
                    ):
                    raise exc.DoNotOverwrite(
                        "Aborting because we don't wish to overwrite %s." % \
                        testname
                    )
                for each in os.listdir(filename):
                    if each.split('.')[-1] in ('png', 'json'):
                        os.remove(os.path.join(filename, each))
                for each in os.listdir(os.path.join(filename, 'last')):
                    if each.split('.')[-1] == 'png':
                        os.remove(os.path.join(filename, 'last', each))
    else:
        if mode == modes.RECORD:
            os.makedirs(filename)
            os.makedirs(os.path.join(filename, 'last'))
            # todo exc
        else:
            raise exc.EmptyPath('%s does not exist\n' % filename)
    return True

def make_tests(test_files, mode, cwd, data_dir, **kwargs): # pylint: disable=R0914,R0912
    """
    Given a list of huxley test files, a mode, working directory, and
    options as found on the CLI interface, make tests for use by the
    dispatcher.
    """
    from huxley.data import Settings, TestRun

    postdata = _postdata(kwargs.pop('postdata', {}))
    diffcolor = tuple(
        int(x) for x in (kwargs.pop('diffcolor', None) or DEFAULT_DIFFCOLOR).split(',')
    )

    tests = {}
    names = kwargs.pop('names', None)
    overwrite = kwargs.get('overwrite', False)

    for file_name in test_files:

        config = ConfigParser.SafeConfigParser(
            allow_no_value=True
        )
        config.read([file_name])

        for testname in config.sections():

            if names and (testname not in names):
                continue
            if testname in tests:
                log.debug('Duplicate test name %s', testname)
                return exits.ERROR

            test_config = dict(config.items(testname))

            url = test_config.get('url', None)
            if not url:
                raise exc.InvalidHuxleyfile(
                    '%s did not have a `url` argument' % testname
                )

            cookies = test_config.get('cookies', None)
            if cookies and len(cookies) > 0:
                cookies = json.loads(cookies)
            else:
                cookies = None

            browser = test_config.get('browser', None)
            if browser:
                if kwargs['browser'] != browser:
                    raise exc.DifferentBrowser(
                        "Different browser given in command-line than "
                        "is on recorded run. Screenshots may not match, "
                        "so aborting. Please re-record."
                    )
            if kwargs['browser']:
                browser = kwargs['browser']

            default_filename = os.path.join(
                data_dir,
                testname
            )
            filename = test_config.get(
                'filename',
                default_filename
            )
            if not os.path.isabs(filename):
                filename = os.path.join(cwd, filename)

            verify_and_prepare_files(filename, testname, mode, overwrite)

            # load recorded runs if appropriate
            if mode != modes.RECORD:
                recorded_run = read_recorded_run(os.path.join(filename, 'record.json'))
            else:
                recorded_run = None

            screensize = tuple(
                int(x) for x in
                    (kwargs.pop('screensize', None) or \
                    test_config.get('screensize', '1024x768')
            ).split('x'))

            settings = Settings(
                name=testname,
                desc=test_config.get('desc', None),
                url=url,
                mode=mode,
                path=filename,
                browser=browser,
                screensize=screensize,
                postdata=postdata or test_config.get('postdata'),
                diffcolor=diffcolor,
                save_diff=kwargs.pop('save_diff', None),
                cookies=cookies
            )

            tests[testname] = TestRun(settings, recorded_run)

    return tests

