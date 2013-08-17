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

import ConfigParser
import glob
import json
import os
import sys

import plac
from selenium import webdriver

from huxley.main import main as huxleymain
from huxley.version import __version__


class ExitCodes(object):
    OK = 0
    NEW_SCREENSHOTS = 1
    ERROR = 2


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


DEFAULT_WEBDRIVER = 'http://localhost:4444/wd/hub'
DEFAULT_SLEEPFACTOR = 1.0
DEFAULT_SCREENSIZE = '1024x768'
DEFAULT_BROWSER = 'firefox'
DEFAULT_DIFFCOLOR = '0,255,0'

LOCAL_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_LOCAL', DEFAULT_WEBDRIVER)
REMOTE_WEBDRIVER_URL = os.environ.get('HUXLEY_WEBDRIVER_REMOTE', DEFAULT_WEBDRIVER)
DEFAULTS = json.loads(os.environ.get('HUXLEY_DEFAULTS', 'null'))


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
    playback_only = plac.Annotation(
        'Don\'t write new screenshots',
        'flag', 'p'
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

    sleepfactor = plac.Annotation(
        'Sleep interval multiplier',
        'option', 's', float,
        metavar=DEFAULT_SLEEPFACTOR
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

    autorerecord = plac.Annotation(
        'Playback test and automatically rerecord if it fails',
        'flag', 'a' # todo
    ),

    version = plac.Annotation(
        'Get the current version',
        'flag', 'v'
    )
)
def _main(
        names=None,
        testfile='Huxleyfile',
        record=False,
        rerecord=False,
        playback_only=False,
        local=None,
        remote=None,
        postdata=None,
        sleepfactor=None,
        browser=None,
        screensize=None,
        diffcolor=None,
        save_diff=False,
        autorerecord=False,
        version=False
    ):

    if version:
        print 'Huxley ' + __version__
        return ExitCodes.OK

    test_files = glob.glob(testfile)
    if len(test_files) == 0:
        print 'no Huxleyfile found'
        return ExitCodes.ERROR

    if record and rerecord: # todo
        raise Exception("Can't have both, TODO")

    if postdata:
        if postdata == '-':
            postdata = sys.stdin.read()
        else:
            with open(postdata, 'r') as f:
                postdata = json.loads(f.read())

    if local and not remote:
        driver_url = local
    else:
        driver_url = remote or REMOTE_WEBDRIVER_URL
    try:
        driver = webdriver.Remote(driver_url, CAPABILITIES[(browser or DEFAULT_BROWSER)])
        screensize = tuple(int(x) for x in (screensize or DEFAULT_SCREENSIZE).split('x'))
    except KeyError:
        raise ValueError(
            'Invalid browser %r; valid browsers are %r.' % (browser, DRIVERS.keys())
        )

    diffcolor = tuple(int(x) for x in (diffcolor or DEFAULT_DIFFCOLOR).split(','))

    new_screenshots = False

    for file_name in test_files:
        msg = 'Running Huxley file: ' + file_name
        print '-' * len(msg)
        print msg
        print '-' * len(msg)

        config = ConfigParser.SafeConfigParser(
            defaults=DEFAULTS,
            allow_no_value=True
        )

        config.read([file_name])
        for testname in config.sections():
            if names and (testname not in names):
                continue
            print 'Running test:', testname
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
            sleepfactor = sleepfactor or float(test_config.get(
                'sleepfactor',
                1.0
            ))
            postdata = postdata or test_config.get(
                'postdata'
            )
            screensize = screensize or test_config.get(
                'screensize',
                '1024x768'
            )
            if record:
                run = huxleymain(
                    url,
                    filename,
                    postdata,
                    local=LOCAL_WEBDRIVER_URL,
                    remote=REMOTE_WEBDRIVER_URL,
                    browser=browser,
                    sleepfactor=sleepfactor, # todo not used
                    record=True,
                    screensize=screensize,
                    driver=driver
                )
            else:
                run = huxleymain(
                    url,
                    filename,
                    postdata,
                    remote=REMOTE_WEBDRIVER_URL,
                    browser=browser,
                    sleepfactor=sleepfactor,
                    autorerecord=not playback_only,
                    save_diff=save_diff,
                    screensize=screensize,
                    driver=driver
                )
            new_screenshots = new_screenshots or (run != 0)
            print

    if new_screenshots:
        print '** New screenshots were written; please verify that they are correct. **'
        return ExitCodes.NEW_SCREENSHOTS
    else:
        return ExitCodes.OK

def main():
    sys.exit(plac.call(_main))
