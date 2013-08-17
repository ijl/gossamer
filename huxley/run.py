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
    def __init__(self, screen_size):
        self.steps = []
        self.screen_size = screen_size


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

    @classmethod
    def rerecord(cls, test, path, url, driver, sleepfactor, diffcolor, save_diff):
        print 'Begin rerecord'
        run = TestRun(test, path, url, driver, TestRunModes.RERECORD, diffcolor, save_diff)
        run._playback(sleepfactor)
        print
        print 'Playing back to ensure the test is correct'
        print
        cls.playback(test, path, url, driver, sleepfactor, diffcolor, save_diff)

    @classmethod
    def playback(cls, test, path, url, driver, sleepfactor, diffcolor, save_diff):
        print 'Begin playback'
        run = TestRun(test, path, url, driver, TestRunModes.PLAYBACK, diffcolor, save_diff)
        run._playback(sleepfactor)

    def _playback(self, sleepfactor):
        self.driver.set_window_size(*self.test.screen_size)
        navigate(self.driver, self.url)
        last_offset_time = 0
        for step in self.test.steps:
            sleep_time = (step.offset_time - last_offset_time) * sleepfactor
            print '  Sleeping for', sleep_time, 'ms'
            time.sleep(float(sleep_time) / 1000)
            step.execute(self)
            last_offset_time = step.offset_time

    @classmethod
    def record(cls, driver, remote_driver, url, screen_size, path, diffcolor, sleepfactor, save_diff):
        print 'Begin record'
        try:
            os.makedirs(path)
        except:
            pass
        test = Test(screen_size)
        run = TestRun(test, path, url, driver, TestRunModes.RECORD, diffcolor, save_diff)
        driver.set_window_size(*screen_size)
        navigate(driver, url)
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
            if len(raw_input("Press enter to take a screenshot, or type Q+enter if you're done\n")) > 0:
                break
            screenshot_step = ScreenshotTestStep(driver.execute_script('return Date.now();') - start_time, run, len(steps))
            run.driver.save_screenshot(screenshot_step.get_path(run))
            steps.append(screenshot_step)
            print len(steps), 'screenshots taken'

        # now capture the events
        try:
            events = driver.execute_script('return window._getHuxleyEvents();')
        except:
            raise TestError(
                'Could not call window._getHuxleyEvents(). ' +
                'This usually means you navigated to a new page, which is currently unsupportedriver.'
            )
        for (timestamp, type, params) in events:
            if type == 'click':
                steps.append(ClickTestStep(timestamp - start_time, params))
            elif type == 'keyup':
                steps.append(KeyTestStep(timestamp - start_time, params))

        steps.sort(key=operator.attrgetter('offset_time'))

        test.steps = steps

        print
        raw_input(
            'Up next, we\'ll re-run your actions to generate screenshots ' +
            'to ensure they are pixel-perfect when running automatedriver. ' +
            'Press enter to start.'
        )
        print
        cls.rerecord(test, path, url, remote_driver, sleepfactor, diffcolor, save_diff)

        return test

