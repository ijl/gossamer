"""
Record, playback, &c a given test.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import operator
import time

from selenium.common.exceptions import WebDriverException

from gossamer.constant import states, DATA_VERSION
from gossamer.step import Screenshot, Click, Key, Scroll, Text, Navigate
from gossamer.data import Point, Test
from gossamer import util, js, exc

__all__ = ['playback', 'record', 'rerecord', ]


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
        driver.execute_script(js.get_post(href, postdata))
    _load_initial_js(driver)


def _load_initial_js(driver):
    """
    Split from :func:`.navigate` for calling within :func:`.record`
    after a URL change.
    """
    driver.execute_script(js.getGossamerEvents)
    driver.execute_script(js.pageChangingObserver)


def wait_until_loaded(driver):
    """
    Determine that a page has been loaded.
    """
    initial_timeout = 0
    while initial_timeout < 40:
        initial_timeout += 1
        if not driver.execute_script(js.isPageChanging(500)):
            break
        else:
            time.sleep(0.25)
    if initial_timeout == 40:
        raise exc.PlaybackTimeout(
            'Timed out while waiting for the initial load.'
        )


def _process_steps(steps, events, start_time):
    """
    Process events from the user agent into our objects.
    """
    for (timestamp, action, params) in events:
        if action == 'click':
            steps.append(
                Click(timestamp - start_time, Point(*params))
            )
        elif action == 'keyup':
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
                step = step if step.key != '\t' else (steps[i-1] if i !=0 else None)
                if step is not None:
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
            _load_initial_js(driver)
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


def _has_page_changed(url, driver_url):
    """
    Has the page's URL changed? Exclude everything after a hash.
    """
    return \
        url[0:(url.find('#') \
            if url.find('#') > 0 \
            else len(url))]\
        .rstrip('/') \
        != \
        driver_url[0:(driver_url.find('#') \
            if driver_url.find('#') > 0 \
            else len(driver_url))]\
        .rstrip('/')


def record(driver, settings, output):
    """
    Record a given test.
    """
    _begin_browsing(driver, settings)
    start_time = driver.execute_script(js.now)
    url = settings.url
    steps = []
    navs = []
    while True:
        if util.prompt("\nPress enter to take a screenshot, "
            "or type Q if you're done.", ('Q', 'q'), testname=settings.name):
            break
        # detect page changes
        if _has_page_changed(url, driver.current_url):
            navs.append(
                Navigate(
                    driver.execute_script(js.now) - start_time,
                    driver.current_url
                )
            )
            url = driver.current_url
            _load_initial_js(driver)
        output('Taking screenshot ... ', flush=True)
        screenshot_step = Screenshot(
            driver.execute_script(js.now) - start_time,
            len(steps) + 1
        )
        driver.save_screenshot(screenshot_step.get_path(settings))
        steps.append(screenshot_step)
        output(
            '%d screenshot%s in test.\n' % \
            (len(steps), 's' if len(steps) > 1 else '')
        )
    if len(steps) == 0:
        raise exc.NoScreenshotsRecorded(
            'No screenshots recorded for %s--please use at least one\n' % \
                settings.name
        )

    # now capture the events
    events = driver.execute_script('return window._getGossamerEvents();')
    if type(events) in (unicode, str) and events.startswith(
                                    'A script on this page may be busy, '
                                    'or it may have stopped responding.'):
        raise exc.TestError('Event-capturing script was unresponsive.')

    record = Test( # pylint: disable=W0621
        version = DATA_VERSION,
        settings = settings,
        steps = _process_steps(steps + navs, events, start_time)
    )

    util.prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots to "
        "ensure they \nare pixel-perfect when running automated. Press "
        "enter to start.", testname=settings.name
    )
    playback(driver, settings, record, output)

    return record


def rerecord(driver, settings, record, output): # pylint: disable=W0621
    """
    Rerecord a given test. :func:`.playback` handles it based on mode.
    """
    return playback(driver, settings, record, output)


def playback(driver, settings, record, output): # pylint: disable=W0621,R0912
    """
    Playback a given test.
    """
    if settings.desc:
        output("%s ... " % settings.desc, flush=True)
    else:
        output("Playing back %s ... " % settings.name, flush=True)


    _begin_browsing(driver, settings)
    wait_until_loaded(driver)

    state = states.OK
    err = None
    try:
        for step in record.steps:
            step.delayer(driver)
            timeout = 0
            while timeout < 40:
                timeout += 1
                if not driver.execute_script(js.isPageChanging(250)): # milliseconds
                    step.execute(driver, settings)
                    break
                else:
                    time.sleep(0.25)
            if timeout == 40:
                raise exc.PlaybackTimeout(
                    '%s timed out while waiting for the page to be static.' \
                        % settings.name
                )

    except Exception as err: # pylint: disable=W0703
        state = states.ERROR
        if hasattr(err, 'msg') and err.msg.startswith('element not visible'):
            err = exc.ElementNotVisible(
                "Element was not visible when expected during playback. If "
                "your playback depended on a significant rerender having been "
                "done, then make sure you've waited until nothing is changing "
                "before taking a screenshot."
            )

    output('%s\n' % str(state))
    if err:
        output('%s\n' % str(err))
    output(flush=True)
    return state

