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
Utilities.
"""

import os
import sys
import json
import jsonpickle
import ConfigParser

from selenium import webdriver

from huxley import errors

from huxley.consts import modes, exits, \
    DEFAULT_DIFFCOLOR, DEFAULTS, REMOTE_WEBDRIVER_URL


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
    Load a serialized run. TODO in versioning, validation, etc.
    """
    try:
        if os.path.getsize(filename) <= 0:
            raise errors.RecorcedRunEmpty('%s is empty' % filename)
    except OSError:
        raise errors.RecordedRunDoesNotExist('%s does not exist' % filename)
    try:
        with open(os.path.join(filename, 'record.json'), 'r') as fp:
            recorded_run = jsonpickle.decode(fp.read())
        # todo validate
        return recorded_run
    except ValueError as exc:
        raise # todo error
    except Exception as exc:
        raise exc


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
    except Exception as exc: # todo how can this fail
        raise exc
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
        print 'Invalid browser %r; valid browsers are %r.' % (browser, DRIVERS.keys())
        return exits.ARGUMENT_ERROR
    return driver


def prompt(display, options=None):
    """
    Given text as `display` and optionally `options` as an 
    iterable containing acceptable input, returns a boolean 
    of whether the prompt was met.
    """
    inp = raw_input(display)
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


def make_tests(test_files, mode, cwd, **kwargs):
    """
    Given a list of huxley test files, a mode, working directory, and 
    options as found on the CLI interface, make tests for use by the 
    dispatcher.
    """
    from huxley.cmdline import Settings, TestRun # TODO move classes

    postdata = _postdata(kwargs.pop('postdata'))
    diffcolor = tuple(int(x) for x in (kwargs.pop('diffcolor') or DEFAULT_DIFFCOLOR).split(','))

    tests = {}
    names = kwargs.pop('names')

    for file_name in test_files:

        config = ConfigParser.SafeConfigParser(
            defaults=DEFAULTS,
            allow_no_value=True
        )
        config.read([file_name])

        for testname in config.sections():

            if names and (testname not in names):
                continue
            if testname in tests:
                print 'Duplicate test name %s' % testname
                return exits.ERROR

            test_config = dict(config.items(testname))
            url = config.get(testname, 'url')

            default_filename = os.path.join(
                os.path.dirname(file_name),
                testname + '.huxley'
            )
            filename = test_config.get(
                'filename',
                default_filename
            )
            if not os.path.isabs(filename):
                filename = os.path.join(cwd, filename)

            if os.path.exists(filename):
                if mode == modes.RECORD: # todo weirdness with rerecord
                    if os.path.getsize(filename) > 0:
                        if not prompt(
                            '%s already exists--clear existing '
                            'screenshots and overwrite test? [Y/n] ' \
                                % testname, 
                            ('Y', 'y')
                            ):
                            return exits.ERROR
                        for each in os.listdir(filename):
                            if each.split('.')[-1] in ('png', 'json'):
                                os.remove(os.path.join(filename, each))
            else:
                if mode == modes.RECORD:
                    try:
                        os.makedirs(filename)
                    except Exception as exc:
                        print str(exc)
                        raise
                else:
                    print '%s does not exist' % filename
                    return exits.ERROR

            # load recorded runs if appropriate
            if mode != modes.RECORD:
                try:
                    recorded_run = read_recorded_run(filename)
                except errors.RecorcedRunEmpty:
                    print 'Recorded run for %s is empty--please rerecord' % \
                        (testname, )
                    return exits.RECORDED_RUN_ERROR
                except errors.RecordedRunDoesNotExist:
                    print 'Recorded run for %s does not exist' % \
                        (testname, )
                    return exits.RECORDED_RUN_ERROR
            else:
                recorded_run = None

            sleepfactor = kwargs.pop('sleepfactor', None) or float(test_config.get(
                'sleepfactor',
                1.0
            ))
            screensize = tuple(int(x) for x in (kwargs.pop('screensize', None) or test_config.get(
                'screensize',
                '1024x768'
            )).split('x'))

            settings = Settings(
                name=testname,
                url=url,
                mode=mode,
                path=filename,
                sleepfactor=sleepfactor,
                screensize=screensize,
                postdata=postdata or test_config.get('postdata'),
                diffcolor=diffcolor,
                save_diff=kwargs.pop('save_diff', None)
            )

            tests[testname] = TestRun(settings, recorded_run)
            # print tests[testname]

    return tests

