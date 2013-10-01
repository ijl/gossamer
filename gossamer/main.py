"""
:func:`.dispatch` runs tests that have already been setup.

Tests can be setup through the command-line interface via
:func:`gossamer.cli.main` and through unittest via
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
    result_log = {name: None for name, _ in tests.items()}
    error_log = {name: None for name, _ in tests.items()}
    try:
        for name, test in tests.items():
            result, err = funcs[mode][0](driver, *funcs[mode][1](test), output=output)
            if (not result or result in (states.FAIL, states.ERROR)) and stop_on_error:
                break
            result_log[name] = result
            error_log[name] = err
            if mode == modes.RECORD:
                # rerecord needs refactor to support writing updated settings
                util.write_recorded_run(test.settings.path, result)
    except exc.NoScreenshotsRecorded:
        raise
    except WebDriverException as exception:
        if 'not reachable' in exception.msg:
            raise exc.WebDriverWentAway('WebDriver cannot be reached.')
        elif 'Cannot find function' in exception.msg:
            raise exc.UnavailableBrowser(
                'WebDriver cannot seem to run the browser you selected. You '
                'may be missing a WebDriver dependency needed for that browser '
                '(e.g., chromium-chromedriver), or may need to use a separate '
                'WebDriver (e.g., InternetExplorerDriver).'
                )
        raise
    except Exception:
        raise
    return (result_log, error_log)
