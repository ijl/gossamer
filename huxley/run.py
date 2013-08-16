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

import sys
import json
import operator
import time

# from huxley.consts import modes
from huxley.errors import TestError, NoScreenshotsRecorded
from huxley.steps import ScreenshotTestStep, ClickTestStep, KeyTestStep
from huxley import util

__all__ = ['playback', 'record', 'rerecord', ]

class Point(object): # pylint: disable=R0903
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


def get_post_js(url, postdata):
    """
    TODO docs
    """
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
    """
    TODO docs
    """
    href, postdata = url
    driver.get('about:blank')
    driver.refresh()
    if not postdata:
        driver.get(href)
    else:
        driver.execute_script(get_post_js(href, postdata))


class Test(object): # pylint: disable=R0903
    """
    Holds steps and screensize... is serialized as record.json. 

    TODO: why only those two attrs?
    """

    def __init__(self, screensize, steps=None):
        self.screensize = screensize
        self.steps = steps or []

    def __repr__(self):
        return "%s: %s %r" % (
            self.__class__.__name__,
            self.screensize,
            self.steps
        )


class TestRun(object): # pylint: disable=R0903
    """
    Specific instance of a test run. Not sure of use now?
    """

    def __init__(self, 
            test, path, url, driver, mode, diffcolor, save_diff
        ): # pylint: disable=R0913
        if not isinstance(test, Test):
            raise ValueError('You must provide a Test instance')
        self.test = test
        self.path = path
        self.url = url
        self.driver = driver
        self.mode = mode
        self.diffcolor = diffcolor
        self.save_diff = save_diff


def rerecord(driver, settings, record): # pylint: disable=W0621
    """
    Rerecord a given test
    """
    # did I break something by removing the driver=remote_driver pass from #record?
    # what does this do?
    sys.stdout.write('Playing back to ensure the test is correct ... ')
    sys.stdout.flush()
    return playback(settings, driver, record)


def process_steps(steps, events):
    """
    process events from the user agent into our objects
    todo: combine multiple scroll events?
    """
    steps = []
    for (timestamp, action, params) in events:
        if action == 'click':
            steps.append(ClickTestStep(timestamp - start_time, Point(*params)))
        elif action == 'keyup':
            steps.append(KeyTestStep(timestamp - start_time, params))

    # TODO, steps: truncate events after last screenshot
    return sorted(steps, key=operator.attrgetter('offset_time'))


_getHuxleyEvents = """
(function() {
    var events = [];

    window.addEventListener(
        'click',
        function (e) { events.push([Date.now(), 'click', [e.clientX, e.clientY]]); },
        true
    );
    window.addEventListener(
        'keyup',
        function (e) { events.push([Date.now(), 'keyup', String.fromCharCode(e.keyCode)]); },
        true
    );
    window.addEventListener(
        'scroll',
        function(e) { events.push([Date.now(), 'scroll', [this.pageXOffset, this.pageYOffset]]); },
        true
    );

    window._getHuxleyEvents = function() { return events };
})();
"""


def record(driver, settings):
    """
    Record a given test.
    """
    driver.set_window_size(*settings.screensize)
    navigate(driver, settings.navigate()) # was just url, not (url, postdata)?
    start_time = driver.execute_script('return Date.now();')
    driver.execute_script(_getHuxleyEvents)

    steps = []
    while True:
        if util.prompt("\nPress enter to take a screenshot, "
            "or type Q if you're done.", ('Q', 'q'), testname=settings.name):
            break
        sys.stdout.write('Taking screenshot ... ')
        sys.stdout.flush()
        screenshot_step = ScreenshotTestStep(
            driver.execute_script('return Date.now();') - start_time, 
            len(steps)
        )
        driver.save_screenshot(screenshot_step.get_path(settings))
        steps.append(screenshot_step)
        sys.stdout.write(
            '%d screenshot%s in test.\n' % \
            (len(steps), 's' if len(steps) > 1 else '')
        )
    if len(steps) == 0:
        raise NoScreenshotsRecorded(
            'No screenshots recorded for %s--please use at least one' % \
                settings.name
        )

    # now capture the events
    try:
        events = driver.execute_script('return window._getHuxleyEvents();')
        # print '-'*70
        # print events
        # print '-'*70
    except:
        # todo fix...
        raise TestError(
            'Could not call window._getHuxleyEvents(). '
            'This usually means you navigated to a new page, '
            'which is currently unsupported.'
        )
    if type(events) in (unicode, str) and events.startswith(
                                    'A script on this page may be busy, '
                                    'or it may have stopped responding.'):
        raise TestError('Event-capturing script was unresponsive.')
    
    record = Test( # pylint: disable=W0621
        screensize = settings.screensize,
        steps = process_steps(steps, events)
    )

    util.prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots to "
        "ensure they \nare pixel-perfect when running automated. Press "
        "enter to start.", testname=settings.name
    )
    rerecord(settings, driver, record)
    sys.stdout.write('ok.\n')

    return record



def playback(driver, settings, record): # pylint: disable=W0621
    """
    Playback a given test.
    """
    if settings.desc:
        sys.stdout.write('%s ... ' % settings.desc)
    else:
        sys.stdout.write('Playing back %s ... ' % settings.name)
    sys.stdout.flush()
    driver.set_window_size(*record.screensize)
    navigate(driver, settings.navigate())
    last_offset_time = 0
    for step in record.steps:
        sleep_time = (step.offset_time - last_offset_time) * settings.sleepfactor
        print '  Sleeping for', sleep_time, 'ms'
        time.sleep(float(sleep_time) / 1000)
        step.execute(driver, settings)
        last_offset_time = step.offset_time
    sys.stdout.write('ok.\n')
    sys.stdout.flush()
    return None

