"""
Command-line interface to the app.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import glob
import os
import sys

import plac # pylint: disable=F0401

from gossamer.main import dispatch
from gossamer.constant import modes, exits, states, \
    DEFAULT_WEBDRIVER, DEFAULT_TESTFILE, \
    DEFAULT_DIFFCOLOR, DEFAULT_SCREENSIZE, \
    DEFAULT_BROWSER
from gossamer import util, exc
from gossamer import __version__


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
        'option', 'p', str,
        metavar=DEFAULT_DIFFCOLOR
    ),

    save_diff = plac.Annotation(
        'Save information about failures as last.png and diff.png',
        'flag', 'e'
    ),

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
        'flag', 'version'
    ),

    verbose = plac.Annotation(
        'Verbosity, with -v as logging.DEBUG',
        'flag', 'v', 'verbose'
    ) # pylint: disable=R0915,R0912,R0911,R0914
)


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
    Gossamer CLI.
    """

    if version:
        sys.stdout.write('Gossamer %s\n' % __version__)
        sys.stdout.flush()
        return exits.OK

    sys.stdout.write('Initializing gossamer and opening WebDriver...\n')
    sys.stdout.flush()

    if verbose:
        util.log = util.logger(__name__, 'DEBUG')

    names = names.split(',') if names else None
    browser = browser or DEFAULT_BROWSER

    cwd = os.getcwd()
    test_files = []
    for pattern in (testfile or DEFAULT_TESTFILE).split(','):
        for name in glob.glob(pattern):
            test_files.append(os.path.join(cwd, name))
    if len(test_files) == 0:
        sys.stdout.write('No Gossamerfile found.\n')
        sys.stdout.flush()
        return exits.ERROR

    # data_dir
    if not data_dir:
        data_dir = os.path.join(os.getcwd(), 'gossamer')
        sys.stdout.write('Default data directory of %s\n' % data_dir)
        sys.stdout.flush()
    else:
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(os.getcwd(), data_dir)

    # mode
    if record and rerecord:
        sys.stdout.write('Cannot specify both -r and -rr\n')
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
        tests = util.make_tests(test_files, mode, data_dir, cwd, **options)
    except exc.DoNotOverwrite as exception:
        sys.stdout.write(str(exception))
        sys.stdout.write('\n')
        sys.stdout.flush()
        return exits.ERROR
    except (exc.RecordedRunDoesNotExist, exc.RecordedRunEmpty,
        exc.CouldNotParseRecordedRun) as exception:
        sys.stdout.write(str(exception))
        sys.stdout.write('\n')
        sys.stdout.flush()
        return exits.RECORDED_RUN_ERROR

    driver = None
    try:
        driver = util.get_driver(browser, local, remote)
        if not driver:
            raise exc.WebDriverConnectionFailed(
            'We cannot connect to the WebDriver %s -- is it running?' % local
        )
        # run the tests
        try:
            logs = dispatch(driver, mode, tests)
        except exc.NoScreenshotsRecorded as exception:
            sys.stdout.write(str(exception))
            sys.stdout.flush()
            return exits.ERROR
        sys.stdout.write('\n')
        sys.stdout.flush()
        if mode == modes.PLAYBACK:
            fails = sum(x is states.FAIL for _, x in logs.items())
            errors = sum(x is states.ERROR for _, x in logs.items())
            if fails > 0 or errors > 0:
                msg = []
                if fails > 0:
                    msg.append('failed=%s' % fails)
                if errors > 0:
                    msg.append('errors=%s' % errors)
                sys.stdout.write(
                    'FAILED (%s)\n' % ', '.join(msg)
                )
                sys.stdout.flush()
                return exits.FAILED
            else:
                sys.stdout.write('OK (ok=%s)\n' % len(logs))
                sys.stdout.flush()
                return exits.OK
        return exits.OK
    finally:
        util.close_driver(driver)


def main():
    """
    Defined as the `gossamer` command in setup.py.

    Runs the argument parser and passes settings to
    :func:`gossamer.main.dispatcher`.
    """
    try:
        sys.exit(plac.call(initialize))
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()
        sys.exit(1)
