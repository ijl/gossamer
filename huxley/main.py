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
:func:`.dispatch` runs tests that have already been setup.

Tests can be setup through the command-line interface via 
:func:`huxley.cmdline.main` and through unittest via 
:class:`huxley.integration.HuxleyTestCase`.
"""

from huxley.consts import modes
from huxley import run
from huxley import util
from huxley import errors


def dispatch(driver, mode, tests):
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
            run_log[name] = output
            if mode in (modes.RECORD, modes.RERECORD):
                util.write_recorded_run(test.settings.path, output)
    except errors.NoScreenshotsRecorded:
        raise
    return run_log
