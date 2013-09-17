"""
:func:`.dispatch` runs tests that have already been setup.

Tests can be setup through the command-line interface via
:func:`huxley.cmdline.main` and through unittest via
:class:`huxley.integration.HuxleyTestCase`.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

from huxley.constant import modes, states
from huxley import run, util, exc


def dispatch(driver, mode, tests, stop_on_error=False):
    """
    Given driver and a list of tests, dispatch the appropriate runs and
    return an exit code. For consumption by the CLI and unittest
    integration.
    """
    funcs = {
        modes.RECORD: (run.record, lambda x: (x.settings, )),
        modes.RERECORD: (run.rerecord, lambda x: (x.settings, x.recorded_run)),
        modes.PLAYBACK: (run.playback, lambda x: (x.settings, x.recorded_run))
    }
    run_log = {name: None for name, _ in tests.iteritems()}
    try:
        for name, test in tests.iteritems():
            output = funcs[mode][0](driver, *funcs[mode][1](test))
            if not output or output in (states.FAIL, states.ERROR) and stop_on_error:
                break
            run_log[name] = output
            if mode in (modes.RECORD, modes.RERECORD):
                util.write_recorded_run(test.settings.path, output)
    except exc.NoScreenshotsRecorded:
        raise
    return run_log
