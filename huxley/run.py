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

"""
Record, playback, &c a given test.
"""

import json
import operator
import time

# from huxley.consts import modes
from huxley.errors import TestError, NoStepsRecorded
from huxley.steps import ScreenshotTestStep, ClickTestStep, KeyTestStep

__all__ = ['playback', 'record', 'rerecord', ]

class Point(object):
    """
    Contains validated x, y coordinates for screen position.
    """

    def __init__(self, x, y):
        """
        Stores x and y coordinates. They cannot be negative.
        """
        if x < 0 or y < 0:
            raise ValueError(
                'Coordinates [%s, %s] cannot be negative' % (x, y)
            )
        self.x = x
        self.y = y

    def __repr__(self):
        return ''.join(('[', str(self.x), ', ', str(self.y), ']'))


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


def get_post_js(url, postdata):
    markup = '<form method="post" action="%s">' % url
    for k in postdata.keys():
        markup += '<input type="hidden" name="%s" />' % k
    markup += '</form>'

    js = 'var container = document.createElement("div"); container.innerHTML = %s;' \
            % json.dumps(markup)

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
    """
    Holds steps and screensize... is serialized as record.json. 

    TODO: why only those two attrs?
    """

    def __init__(self, screensize, steps=None):
        self.screensize = screensize
        self.steps = steps or []


class TestRun(object):
    """
    Specific instance of a test run. Not sure of use now?
    """

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


def rerecord(driver, settings, record):
    """
    Rerecord a given test
    """
    # did I break something by removing the driver=remote_driver pass from #record?
    # what does this do?
    print
    print 'Playing back to ensure the test is correct'
    print
    return playback(settings, driver, record)


def record(driver, settings):
    """
    Record a given test.
    """
    print 'Begin record'
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
            len(steps)
        )
        driver.save_screenshot(screenshot_step.get_path(settings))
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
    for (timestamp, action, params) in events:
        if action == 'click':
            steps.append(ClickTestStep(timestamp - start_time, Point(*params)))
        elif action == 'keyup':
            steps.append(KeyTestStep(timestamp - start_time, params))

    if len(steps) == 0:
        raise NoStepsRecorded('TODO something about this')

    record = Test(
        screensize=settings.screensize,
        steps = sorted(steps, key=operator.attrgetter('offset_time'))
    )

    prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots "
        "to ensure they are pixel-perfect when running automated." 
        "Press enter to start."
    )
    print rerecord(settings, driver, record)

    return record



def playback(driver, settings, record):
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
    return None

