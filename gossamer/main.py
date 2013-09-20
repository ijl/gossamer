"""
:func:`.dispatch` runs tests that have already been setup.

Tests can be setup through the command-line interface via
:func:`gossamer.cmdline.main` and through unittest via
:class:`gossamer.integration.GossamerTestCase`.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

from selenium.common.exceptions import WebDriverException

from gossamer.constant import modes, states
from gossamer import run, exc, util


def dispatch(driver, mode, tests, output=None, stop_on_error=False):
    """
    Given driver and a list of tests, dispatch the appropriate runs and
    return an exit code. For consumption by the CLI and unittest
    integration.
    """
    if not output:
        output = util.stdout_writer
    funcs = {
        modes.RECORD: (run.record, lambda x: (x.settings, )),
        modes.RERECORD: (run.rerecord, lambda x: (x.settings, x.steps)),
        modes.PLAYBACK: (run.playback, lambda x: (x.settings, x.steps))
    }
    run_log = {name: None for name, _ in tests.iteritems()}
    try:
        for name, test in tests.iteritems():
            output = funcs[mode][0](driver, *funcs[mode][1](test), output=output)
            if (not output or output in (states.FAIL, states.ERROR)) and stop_on_error:
                break
            run_log[name] = output
            if mode == modes.RECORD:
                util.write_recorded_run(test.settings.path, output)
    except exc.NoScreenshotsRecorded:
        raise
    except WebDriverException as err:
        if 'not reachable' in err.msg:
            raise exc.WebDriverWentAway('WebDriver cannot be reached.')
        elif 'Cannot find function' in err.msg:
            raise exc.UnavailableBrowser(
                'WebDriver cannot seem to run the browser you selected. You '
                'may be missing a WebDriver dependency needed for that browser '
                '(e.g., chromium-chromedriver), or may need to use a separate '
                'WebDriver (e.g., InternetExplorerDriver).'
                )
        raise
    except Exception:
        raise
    return run_log
