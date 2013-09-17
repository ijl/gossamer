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
Command-line interface to the app.
"""

import glob
import os
import sys

import plac

from huxley.consts import modes, exits, \
    DEFAULT_WEBDRIVER, DEFAULT_TESTFILE, \
    DEFAULT_DIFFCOLOR, DEFAULT_SCREENSIZE, \
    DEFAULT_BROWSER
from huxley import util, errors
from huxley.main import dispatch
from huxley.version import __version__


class TestRun(object):  # pylint: disable=R0903
    # check this name...
    """
    Object to be passed into dispatch... containing all information
    to run (and repeat, if persisted) a test.
    """

    def __init__(self, settings, recorded_run=None):
        self.settings = settings
        self.recorded_run = recorded_run

    def __repr__(self):
        return "%s: %r, %r" % (
            self.__class__.__name__,
            self.settings,
            self.recorded_run
        )


class Settings(object): # pylint: disable=R0903,R0902
    """
    Hold validated settings for a specific test run.
    """

    def __init__(self,
            name, url, mode, path, browser,
            screensize, postdata,
            diffcolor, save_diff, cookies=None, desc=None
        ): # pylint: disable=R0913
        self.name = name
        self.url = url
        self.mode = mode
        self.path = path
        self.browser = browser
        self.screensize = screensize
        self.postdata = postdata
        self.diffcolor = diffcolor
        self.save_diff = save_diff
        self.desc = desc
        self.cookies = cookies

    def navigate(self):
        """
        Return data in form expected by :func:`huxley.run.navigate`.
        """
        return (self.url, self.postdata)

    def __repr__(self):
        return '%s: %r' % (self.__class__.__name__, self.__dict__)


@plac.annotations(
    names = plac.Annotation(
        'Test case name(s) to use, comma-separated',
    ),
    postdata = plac.Annotation(
        'File for POST data or - for stdin'
    ),

    testfile = plac.Annotation(
        'Test file(s) to use',
        'option', 'f', str,
        metavar='GLOB'
    ),
    record = plac.Annotation(
        'Record a new test',
        'flag', 'r'
    ),
    rerecord = plac.Annotation(
        'Re-run the test but take new screenshots',
        'flag', 'rr'
    ),
    # playback_only = plac.Annotation(
    #     'Don\'t write new screenshots',
    #     'flag', 'p'
    # ),

    local = plac.Annotation(
        'Local WebDriver URL to use',
        'option', 'l',
        metavar=DEFAULT_WEBDRIVER
    ),
    remote = plac.Annotation(
        'Remote WebDriver to use',
        'option', 'w',
        metavar=DEFAULT_WEBDRIVER
    ),

    browser = plac.Annotation(
        'Browser to use, either firefox, chrome, phantomjs, ie, or opera',
        'option', 'b', str,
        metavar=DEFAULT_BROWSER,
    ),
    screensize = plac.Annotation(
        'Width and height for screen (i.e. 1024x768)',
        'option', 'z',
        metavar=DEFAULT_SCREENSIZE
    ),
    diffcolor = plac.Annotation(
        'Diff color for errors in RGB (i.e. 0,255,0)',
        'option', 'd', str,
        metavar=DEFAULT_DIFFCOLOR
    ),

    save_diff = plac.Annotation(
        'Save information about failures as last.png and diff.png',
        'flag', 'e'
    ),

    # autorerecord = plac.Annotation(
    #     'Playback test and automatically rerecord if it fails',
    #     'flag', 'a' # todo
    # ),

    overwrite = plac.Annotation(
        'Overwrite existing tests without asking',
        'flag', 'o'
    ),

    data_dir = plac.Annotation(
        'Directory in which tests should be stored',
        'option', 'd', str,
    ),

    version = plac.Annotation(
        'Get the current version',
        'flag', 'V', 'version'
    ),

    verbose = plac.Annotation(
        'Verbosity, with -v as logging.DEBUG',
        'flag', 'v', 'verbose'
    )
)

# TODO: when playing back, test if browsers match
#       firefox and chrome do screenshot dimensions differently, for example

def initialize(
        names=None,
        testfile=None,
        record=False,
        rerecord=False,
        local=None,
        remote=None,
        postdata=None,
        browser=None,
        screensize=None,
        diffcolor=None,
        save_diff=False,
        overwrite=False,
        data_dir=None,
        version=False,
        verbose=False
    ): # pylint: disable=R0913,W0613
    """
    Given arguments from the `plac` argument parser, determine the mode and
    test files so tests can be constructed, then pass tests to the
    dispatcher.
    """

    if version:
        sys.stdout.write('Huxley %s\n' % __version__)
        sys.stdout.flush()
        return exits.OK

    sys.stdout.write('Initializing huxley and opening WebDriver...\n')
    sys.stdout.flush()

    if verbose:
        util.log = util.logger(__name__, 'DEBUG')

    names = names.split(',') if names else None

    cwd = os.getcwd()
    test_files = []
    for pattern in (testfile or DEFAULT_TESTFILE).split(','):
        for name in glob.glob(pattern):
            test_files.append(os.path.join(cwd, name))
    if len(test_files) == 0:
        sys.stdout.write('No Huxleyfile found')
        sys.stdout.flush()
        return exits.ERROR

    # data_dir
    if not data_dir:
        data_dir = os.path.join(os.getcwd(), 'huxleeey')
    else:
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(os.getcwd(), data_dir)

    # mode
    if record and rerecord:
        sys.stdout.write('Cannot specify both -r and -rr')
        sys.stdout.flush()
        return exits.ARGUMENT_ERROR
    if record:
        mode = modes.RECORD
    elif rerecord:
        mode = modes.RERECORD
    else:
        mode = modes.PLAYBACK

    attrs = (
        'names', 'local', 'remote', 'postdata',
        'browser', 'screensize', 'diffcolor', 'save_diff', 'overwrite'
    )
    options = {
        key: val for key, val in \
        [(each, locals()[each]) for each in attrs]
    }

    # make tests using the test_files and mode we've resolved to
    try:
        tests = util.make_tests(test_files, mode, cwd, data_dir, **options)
    except errors.DoNotOverwrite as exc:
        sys.stdout.write(str(exc))
        sys.stdout.flush()
        return exits.ERROR
    except (errors.RecordedRunDoesNotExist, errors.RecordedRunEmpty) as exc:
        sys.stdout.write(str(exc))
        sys.stdout.flush()
        return exits.RECORDED_RUN_ERROR

    # driver
    try:
        driver = util.get_driver((browser or DEFAULT_BROWSER), local, remote)
        # run the tests
        try:
            logs = dispatch(driver, mode, tests)
        except errors.NoScreenshotsRecorded as exc:
            sys.stdout.write(str(exc))
            sys.stdout.flush()
            return exits.ERROR
        sys.stdout.write('\n')
        sys.stdout.flush()
        if mode == modes.PLAYBACK:
            failed = sum(x is False for x in logs)
            if failed > 0:
                sys.stdout.write('FAILED (failed=%s)\n' % failed)
                sys.stdout.flush()
            else:
                sys.stdout.write('PASSED (ok=%s)\n' % len(logs))
                sys.stdout.flush()
                exits.OK
        return exits.OK
    finally:
        try:
            driver.quit()
        except UnboundLocalError: # pragma: no cover
            pass

def main():
    """
    Defined as the `huxley` command in setup.py.

    Runs the argument parser and passes settings to
    :func:`huxley.main.dispatcher`.
    """
    sys.exit(plac.call(initialize))
