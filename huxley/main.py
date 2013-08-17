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
Take in configured settings, and run tests and such. Or, it should do this.

For settings initialization, see huxley/cmdline.py
"""

import os

import jsonpickle
from contextlib import closing

from huxley.run import TestRun
from huxley.errors import TestError


def record(settings, driver):
    pass


def main(
        url,
        filename,
        postdata=None,
        record=False,
        rerecord=False,
        sleepfactor=1.0,
        browser=None,
        remote=None,
        local=None,
        diffcolor=None,
        screensize=None,
        autorerecord=False,
        save_diff=False,
        driver=None,
        settings=None
    ):

    # TODO: not do this here; handle non-empty dir, incl. 0-length .json file as failed record
    try:
        os.makedirs(filename)
    except:
        pass

    # TODO: not load json here
    # TODO: paths that (1) read existing JSON and (2) write new JSON should be separated
    #       so we handle duplicate tests etc. in CLI setup
    jsonfile = os.path.join(filename, 'record.json')

    with closing(driver) as driver:
        if record:
            with open(jsonfile, 'w') as f:
                f.write(
                    jsonpickle.encode(
                        TestRun.record(driver, (url, postdata), screensize, filename, diffcolor, sleepfactor, save_diff)
                    )
                )
            print 'Test recorded successfully'
            return 0
        elif rerecord:
            with open(jsonfile, 'r') as f:
                TestRun.rerecord(jsonpickle.decode(f.read()), filename, (url, postdata), driver, sleepfactor, diffcolor, save_diff)
                print 'Test rerecorded successfully'
                return 0
        elif autorerecord:
            with open(jsonfile, 'r') as f:
                test = jsonpickle.decode(f.read())
            try:
                print 'Running test to determine if we need to rerecord'
                TestRun.playback(test, filename, (url, postdata), driver, sleepfactor, diffcolor, save_diff)
                print 'Test played back successfully'
                return 0
            except TestError:
                print 'Test failed, rerecording...'
                TestRun.rerecord(test, filename, (url, postdata), driver, sleepfactor, diffcolor, save_diff)
                print 'Test rerecorded successfully'
                return 2
        else:
            with open(jsonfile, 'r') as f:
                TestRun.playback(jsonpickle.decode(f.read()), filename, (url, postdata), driver, sleepfactor, diffcolor, save_diff)
                print 'Test played back successfully'
                return 0
