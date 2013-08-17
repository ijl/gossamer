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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or impliedriver.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import operator
import os
import time

from huxley.consts import TestRunModes
from huxley.errors import TestError
from huxley.steps import ScreenshotTestStep, ClickTestStep, KeyTestStep

__all__ = ['playback', 'record', 'rerecord', ]

class Point(object):

    def __init__(self, x, y):
        if x < 0 or y < 0:
            raise ValueError(
                'Coordinates [%s, %s] cannot be negative' % (x, y)
            )
        self.x = x
        self.y = y

    def __repr__(self):
        return ''.join(('[', str(self.x), ', ', str(self.y), ']'))


def prompt(display, options=None):
    inp = raw_input(display)
    if options:
        if inp in options:
            return True
        return False
    return True


def get_post_js(url, postdata):
    markup = '<form method="post" action="%s">' % url
    for k in postdata.keys():
        markup += '<input type="hidden" name="%s" />' % k
    markup += '</form>'

    js = 'var container = document.createElement("div"); container.innerHTML = %s;' % json.dumps(markup)

    for (i, v) in enumerate(postdata.values()):
        if not isinstance(v, basestring):
            # TODO: is there a cleaner way to do this?
            v = json.dumps(v)
        js += 'container.children[0].children[%d].value = %s;' % (i, json.dumps(v))

    js += 'document.body.appendChild(container);'
    js += 'container.children[0].submit();'
    return '(function(){ ' + js + '; })();'


def navigate(driver, url):
    href, postdata = url
    driver.get('about:blank')
    driver.refresh()
    if not postdata:
        driver.get(href)
    else:
        driver.execute_script(get_post_js(href, postdata))


class Test(object):
    def __init__(self, screensize):
        self.steps = []
        self.screensize = screensize


class TestRun(object):
    def __init__(self, test, path, url, driver, mode, diffcolor, save_diff):
        if not isinstance(test, Test):
            raise ValueError('You must provide a Test instance')
        self.test = test
        self.path = path
        self.url = url
        self.driver = driver
        self.mode = mode
        self.diffcolor = diffcolor
        self.save_diff = save_diff


def rerecord(settings, driver, record):
    """
    Rerecord a given test
    """
    # did I break something by removing the driver=remote_driver pass from #record?
    print
    print 'Playing back to ensure the test is correct'
    print
    playback(settings, driver, record)


def record(settings, driver):
    """
    Record a given test.
    """
    print 'Begin record'
    try:
        os.makedirs(settings.path) # todo doesn't belong here
    except:
        pass
    record = Test(settings.screensize)
    run = TestRun(
        record,
        settings.path,
        settings.url,
        driver,
        TestRunModes.RECORD,
        settings.diffcolor,
        settings.save_diff
    )
    driver.set_window_size(*settings.screensize)
    navigate(driver, settings.navigate()) # was just url, not (url, postdata)?
    start_time = driver.execute_script('return Date.now();')
    driver.execute_script('''
(function() {
var events = [];
window.addEventListener('click', function (e) { events.push([Date.now(), 'click', [e.clientX, e.clientY]]); }, true);
window.addEventListener('keyup', function (e) { events.push([Date.now(), 'keyup', String.fromCharCode(e.keyCode)]); }, true);
window._getHuxleyEvents = function() { return events; };
})();
''')
    steps = []
    while True:
        if prompt("Press enter to take a screenshot, "
            "or type Q+enter if you're done\n", ('Q', 'q')):
            break
        screenshot_step = ScreenshotTestStep(
            driver.execute_script('return Date.now();') - start_time, 
            run, 
            len(steps)
        )
        run.driver.save_screenshot(screenshot_step.get_path(run))
        steps.append(screenshot_step)
        print len(steps), 'screenshots taken'

    # now capture the events
    try:
        events = driver.execute_script('return window._getHuxleyEvents();')
    except:
        raise TestError(
            'Could not call window._getHuxleyEvents(). '
            'This usually means you navigated to a new page, '
            'which is currently unsupported.'
        )
    for (timestamp, type, params) in events:
        if type == 'click':
            steps.append(ClickTestStep(timestamp - start_time, Point(*params)))
        elif type == 'keyup':
            steps.append(KeyTestStep(timestamp - start_time, params))

    if len(steps) == 0:
        raise Exception('TODO something about this')

    record.steps = sorted(steps, key=operator.attrgetter('offset_time'))

    prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots "
        "to ensure they are pixel-perfect when running automated." 
        "Press enter to start."
    )
    print rerecord(settings, driver, record)

    return record



def playback(settings, driver, record):
    """
    Playback a given test.
    """
    driver.set_window_size(*record.screensize)
    navigate(driver, settings.navigate())
    last_offset_time = 0
    for step in record.steps:
        sleep_time = (step.offset_time - last_offset_time) * settings.sleepfactor
        print '  Sleeping for', sleep_time, 'ms'
        time.sleep(float(sleep_time) / 1000)
        step.execute(driver, settings)
        last_offset_time = step.offset_time
    return 0