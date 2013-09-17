"""
Record, playback, &c a given test.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import sys
import json
import operator
import time

from selenium.common.exceptions import WebDriverException # pylint: disable=F0401

from huxley.constant import states
from huxley.step import Screenshot, Click, Key, Scroll, Text
from huxley.data import Point, Test
from huxley import util, js, exc

__all__ = ['playback', 'record', 'rerecord', ]


def get_post_js(url, postdata):
    """
    Retrieve data for navigate.
    """
    markup = '\n'.join([
        '<form method="post" action="%s">' % url,
        '\n'.join(['<input type="hidden" name="%s" />' % k for k in postdata.keys()]),
        '</form>'
    ])

    script = 'var container = document.createElement("div"); container.innerHTML = %s;' \
            % json.dumps(markup)

    for (i, v) in enumerate(postdata.values()):
        if not isinstance(v, basestring):
            v = json.dumps(v)
        script += 'container.children[0].children[%d].value = %s;' % (i, json.dumps(v))

    script += 'document.body.appendChild(container);'
    script += 'container.children[0].submit();'
    return '(function(){ ' + script + '; })();'


def navigate(driver, url):
    """
    Navigate the driver to the given URL.
    """
    href, postdata = url
    driver.get('about:blank')
    driver.refresh()
    if not postdata:
        driver.get(href)
    else:
        driver.execute_script(get_post_js(href, postdata))


def rerecord(driver, settings, record): # pylint: disable=W0621
    """
    Rerecord a given test
    """
    return playback(driver, settings, record)


def _process_steps(steps, events, start_time):
    """
    process events from the user agent into our objects
    todo: combine multiple scroll events?
    """
    for (timestamp, action, params) in events:
        if action == 'click':
            steps.append(
                Click(timestamp - start_time, Point(*params))
            )
        elif action == 'keyup':
            util.log.debug('keyup: %r', params)
            steps.append(
                Key(
                    timestamp - start_time,
                    key=params[0], shift=params[1],
                    eid=params[2][0], eid_val=params[2][1],
                    ecn=params[3][0], ecn_val=params[3][1],
                    ecl=params[4][0], ecl_val=params[4][1]
                )
            )
        elif action == 'scroll':
            steps.append(
                Scroll(timestamp - start_time, Point(*params))
            )

    # iterate through steps, and process 'raw' steps like Key into Text
    last_screenshot_time = None
    merges = []
    length = len(steps) - 1
    for i, step in enumerate(steps):
        if isinstance(step, Screenshot):
            last_screenshot_time = step.offset_time
        if isinstance(step, Key):
            if i != length and step.key != '\t' and isinstance(steps[i+1], Key):
                continue
            else:
                # tab keyup carries the element of the new field, so go back one
                step = step if step.key != '\t' else steps[i-1]
                merges.append(
                    Text(
                        offset_time=step.offset_time,
                        value=step.value,
                        identifier_type=step.identifier_type,
                        identifier=step.identifier
                    )
                )
        # not merging scrolls; might've been done for rendering side effects

    def _filter_steps(step):
        """
        Filter for whether a given step should go to playback.
        """
        return step.offset_time <= last_screenshot_time and \
            step.playback is True

    steps = sorted(
        filter(_filter_steps, steps + merges), # pylint: disable=W0141
        key=operator.attrgetter('offset_time')
    )
    util.log.debug('filtered steps: %r', steps)
    return steps

def _begin_browsing(driver, settings):
    """
    Prepare the browser for the test to begin.
    """
    try:
        driver.delete_all_cookies()
        driver.set_window_size(*settings.screensize)
        navigate(driver, settings.navigate())
        if settings.cookies is not None and len(settings.cookies) > 0:
            for cookie in settings.cookies:
                driver.add_cookie(cookie)
            # selenium issue forces us to go to the domain in question
            # before setting a cookie for it -- so this assumes
            # we get only one domain in cookies.
            # https://code.google.com/p/selenium/issues/detail?id=1953
            # todo: validate len(cookie) == 1 on import
            driver.refresh()
    except WebDriverException as exception:
        if exception.msg.startswith("Error communicating with the remote browser"):
            raise exc.WebDriverWentAway(
                "Cannot connect to the WebDriver browser: %s" % str(exception)
            )
        elif exception.msg.startswith("<unknown>: SecurityError: DOM Exception"):
            raise exc.WebDriverSecurityError(
                "WebDriver experienced a security error: %s" % str(exception)
            )
        raise


def record(driver, settings):
    """
    Record a given test.
    """
    _begin_browsing(driver, settings)
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
            len(steps) + 1
        )
        driver.save_screenshot(screenshot_step.get_path(settings))
        steps.append(screenshot_step)
        sys.stdout.write(
            '%d screenshot%s in test.\n' % \
            (len(steps), 's' if len(steps) > 1 else '')
        )
    if len(steps) == 0:
        raise exc.NoScreenshotsRecorded(
            'No screenshots recorded for %s--please use at least one' % \
                settings.name
        )

    # now capture the events
    try:
        events = driver.execute_script('return window._getHuxleyEvents();')
    except:
        # todo fix...
        raise exc.TestError(
            'Could not call window._getHuxleyEvents(). '
            'This usually means you navigated to a new page, '
            'which is currently unsupported.'
        )
    if type(events) in (unicode, str) and events.startswith(
                                    'A script on this page may be busy, '
                                    'or it may have stopped responding.'):
        raise exc.TestError('Event-capturing script was unresponsive.')

    record = Test( # pylint: disable=W0621
        browser = settings.browser,
        screensize = settings.screensize,
        steps = _process_steps(steps, events, start_time)
    )

    util.prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots to "
        "ensure they \nare pixel-perfect when running automated. Press "
        "enter to start.", testname=settings.name
    )
    rerecord(driver, settings, record)

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

    _begin_browsing(driver, settings)
    driver.execute_script(js.pageChangingObserver)

    time.sleep(2.5) # todo, initial load

    state = states.OK
    err = None
    try:
        for step in record.steps:

            step.delayer(driver)

            timeout = 0
            while timeout < 150:
                if not driver.execute_script(js.isPageChanging(250)): # milliseconds
                    step.execute(driver, settings)
                    break
                else:
                    timeout += 1
            if timeout == 150:
                raise exc.PlaybackTimeout(
                    '%s timed out while waiting for the page to be static.' \
                        % settings.name
                )

    except Exception as err: # pylint: disable=W0703
        state = states.ERROR
        if err.msg and err.msg.startswith('element not visible'):
            err = exc.ElementNotVisible(
                "Element was not visible when expected during playback. If "
                "your playback depended on a significant rerender having been "
                "done, try recording a bit slower."
            )

    sys.stdout.write('%s\n' % str(state))
    if err:
        sys.stdout.write('%s\n' % str(err))
    sys.stdout.flush()
    return state

