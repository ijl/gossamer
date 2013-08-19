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
from huxley.steps import Screenshot, Click, Key, Scroll
from huxley import util, js, errors

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

    script = 'var container = document.createElement("div"); container.innerHTML = %s;' \
            % json.dumps(markup)

    for (i, v) in enumerate(postdata.values()):
        if not isinstance(v, basestring):
            # TODO: is there a cleaner way to do this?
            v = json.dumps(v)
        script += 'container.children[0].children[%d].value = %s;' % (i, json.dumps(v))

    script += 'document.body.appendChild(container);'
    script += 'container.children[0].submit();'
    return '(function(){ ' + script + '; })();'


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

    def __init__(self, browser, screensize, steps=None):
        self.browser = browser
        self.screensize = screensize
        self.steps = steps or []

    def __repr__(self):
        return "%s: %s %s %r" % (
            self.__class__.__name__,
            self.browser,
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
    return playback(settings, driver, record)


def process_steps(steps, events, start_time):
    """
    process events from the user agent into our objects
    todo: combine multiple scroll events?
    """
    for (timestamp, action, params) in events:
        if action == 'click':
            steps.append(Click(timestamp - start_time, Point(*params)))
        elif action == 'keyup':
            steps.append(Key(timestamp - start_time, key=params[0], shift=params[1], eid=params[2], ecn=params[3], ecl=params[4]))
        elif action == 'scroll':
            steps.append(Scroll(timestamp - start_time, Point(*params)))

    # TODO, steps: truncate events after last screenshot
    return sorted(steps, key=operator.attrgetter('offset_time'))


def record(driver, settings):
    """
    Record a given test.
    """
    driver.delete_all_cookies()
    driver.set_window_size(*settings.screensize)
    navigate(driver, settings.navigate()) # was just url, not (url, postdata)?
    start_time = driver.execute_script(js.now)
    driver.execute_script(js.getHuxleyEvents)
    driver.execute_script(js.pageChangingObserver)

    steps = []
    while True:
        if util.prompt("\nPress enter to take a screenshot, "
            "or type Q if you're done.", ('Q', 'q'), testname=settings.name):
            break
        sys.stdout.write('Taking screenshot ... ')
        sys.stdout.flush()
        screenshot_step = Screenshot(
            driver.execute_script(js.now) - start_time, 
            len(steps)
        )
        driver.save_screenshot(screenshot_step.get_path(settings))
        steps.append(screenshot_step)
        sys.stdout.write(
            '%d screenshot%s in test.\n' % \
            (len(steps), 's' if len(steps) > 1 else '')
        )
    if len(steps) == 0:
        raise errors.NoScreenshotsRecorded(
            'No screenshots recorded for %s--please use at least one' % \
                settings.name
        )

    # now capture the events
    try:
        events = driver.execute_script('return window._getHuxleyEvents();')
        print events
    except:
        # todo fix...
        raise errors.TestError(
            'Could not call window._getHuxleyEvents(). '
            'This usually means you navigated to a new page, '
            'which is currently unsupported.'
        )
    if type(events) in (unicode, str) and events.startswith(
                                    'A script on this page may be busy, '
                                    'or it may have stopped responding.'):
        raise errors.TestError('Event-capturing script was unresponsive.')
    
    record = Test( # pylint: disable=W0621
        browser = settings.browser,
        screensize = settings.screensize,
        steps = process_steps(steps, events, start_time)
    )

    util.prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots to "
        "ensure they \nare pixel-perfect when running automated. Press "
        "enter to start.", testname=settings.name
    )
    rerecord(settings, driver, record)

    return record


def playback(driver, settings, record): # pylint: disable=W0621
    """
    Playback a given test.
    """
    if settings.desc:
        sys.stdout.write('%s ... ' % settings.desc)
    else:
        sys.stdout.write('Playing back %s ... ' % settings.name) # todo huxleyfile.name
    sys.stdout.flush()

    try:
        driver.delete_all_cookies()
        driver.set_window_size(*record.screensize)
        navigate(driver, settings.navigate())
        driver.execute_script(js.pageChangingObserver)
    except Exception:
        # TODO: webdriver can become unresponsive
        raise

    time.sleep(1) # todo, initial load

    passing = True
    try:
        for step in record.steps:

            time.sleep(0.25) # minimum, todo
            if isinstance(step, Screenshot):
                time.sleep(0.75) # careful, todo

            timeout = 0
            while timeout < 150:
                if not driver.execute_script(js.isPageChanging(100)): # milliseconds
                    step.execute(driver, settings)
                    break
                else:
                    timeout += 1
            if timeout == 150:
                raise errors.PlaybackTimeout(
                    '%s timed out while waiting for the page to be static.' % settings.name
                )

    except Exception as exc:
        passing = False
        # todo
        raise

    sys.stdout.write('ok.\n' if passing else 'FAIL.\n')
    sys.stdout.flush()
    return passing

