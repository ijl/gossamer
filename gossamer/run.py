"""
Record, playback, &c a given test.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import operator
import time

from selenium.common.exceptions import WebDriverException

from gossamer.constant import states, modes, DATA_VERSION
from gossamer.step import Screenshot, Click, Key, Scroll, Text, \
    Navigate, Dropdown, KeyParams, ClickParams
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


def _process_steps(steps, events, start_time): # pylint: disable=R0912
    """
    Process events from the user agent into our objects.
    """
    util.log.debug('_process_steps: %s steps, %s events', len(steps), len(events))
    for (timestamp, action, params) in sorted(events, key=lambda x: x[0]):
        util.log.debug('event: %i, %s, %r', timestamp, action, params)
        if action == 'click':
            params = ClickParams(*params)
            if not params[1]:
                steps.append(
                    Click(timestamp - start_time, Point(*params.pos))
                )
            else:
                steps.append(
                    Dropdown(
                        timestamp - start_time,
                        Point(*params.pos),
                        params.eid,
                        params.ecn,
                        params.ecl
                    )
                )
        elif action == 'keyup':
            params = KeyParams(*params)
            steps.append(
                Key(
                    timestamp - start_time,
                    key=params.key, shift=params.shift,
                    eid=params.eid[0], eid_val=params.eid[1],
                    ecn=params.ecn[0], ecn_val=params.ecn[1],
                    ecl=params.ecl[0], ecl_val=params.ecl[1]
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
                step = step if step.key != '\t' else (steps[i-1] if i != 0 else None)
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


class CaptureEvents(object): # pylint: disable=R0903
    """
    Merge new events with old, keeping state of `timestamp`.
    """

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.retry = 3

    def __call__(self, driver, events):
        """
        Capture events many times during a run, and merge them based
        on a composite key of 'timestamp.action'. This is an ugly workaround
        for an apparent Selenium issue.
        """
        timestamp = driver.execute_script(js.now)
        try:
            merges = driver.execute_script('return window._getGossamerEvents();')
        except WebDriverException as exception:
            if exception.msg.startswith('window._getGossamerEvents is not a function'):
                # navigation
                _load_initial_js(driver)
                self.retry -= 1
                if self.retry > 0:
                    return self(driver, events)
            raise
        if type(merges) in (unicode, str) and merges.startswith(
                                        'A script on this page may be busy, or '
                                        'it may have stopped responding.'):
            raise exc.TestError('Event-capturing script was unresponsive.')
        for event in merges:
            if event[0] > self.timestamp:
                events['%s.%s' % (str(event[0]), str(event[1]))] = event
        self.timestamp = timestamp
        return events


def record(driver, settings, output):
    """
    Record a given test.
    """
    _begin_browsing(driver, settings)
    start_time = driver.execute_script(js.now)
    url = settings.url
    steps = []
    navs = []
    events = {}
    get_events = CaptureEvents(start_time)

    while True:
        if util.prompt("\nPress enter to take a screenshot, "
            "or type Q if you're done.", ('Q', 'q'), testname=settings.name):
            break
        events = get_events(driver, events)
        # detect page changes
        if _has_page_changed(url, driver.current_url):
            if (not len(navs) and not settings.expect_redirect):
                # only add to navs if an initial redirect is not expected
                navs.append(
                    Navigate(
                        driver.execute_script(js.now) - start_time,
                        driver.current_url
                    )
                )
            url = driver.current_url
            _load_initial_js(driver)
        events = get_events(driver, events)

        # take screenshot
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

    # must have at least one screenshot
    if len(steps) == 0:
        raise exc.NoScreenshotsRecorded(
            'No screenshots recorded for %s--please take at least one\n' % \
                settings.name
        )

    # final capture of events
    events = get_events(driver, events)
    steps = _process_steps(steps + navs, events.values(), start_time)
    record = Test( # pylint: disable=W0621
        version = DATA_VERSION,
        settings = settings,
        steps = steps
    )

    util.prompt(
        "\n"
        "Up next, we'll re-run your actions to generate screenshots to "
        "ensure they \nare pixel-perfect when running automated. Press "
        "enter to start.", testname=settings.name
    )
    playback(driver, settings, record, output)

    return (record, None)


def rerecord(driver, settings, record, output): # pylint: disable=W0621
    """
    Rerecord a given test. :func:`.playback` handles it based on mode.
    """
    return playback(driver, settings, record, output, modes.RERECORD)


def playback(driver, settings, record, output, mode=None): # pylint: disable=W0621,R0912
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
    mode = mode or modes.PLAYBACK

    try:
        for step in record.steps:
            step.delayer(driver)
            timeout = 0
            while timeout < 40:
                timeout += 1
                if not driver.execute_script(js.isPageChanging(250)): # milliseconds
                    step.execute(driver, settings, mode)
                    break
                else:
                    time.sleep(0.25)
            if timeout == 40:
                raise exc.PlaybackTimeout(
                    '%s timed out while waiting for the page to be static.' \
                        % settings.name
                )

    except Exception as exception: # pylint: disable=W0703
        if isinstance(exception, exc.ScreenshotsDiffer):
            state = states.FAIL
            err = exception
        else:
            state = states.ERROR
            if hasattr(exception, 'msg') and (exception.msg.startswith('element not visible') or
                exception.msg.startswith('Element is not currently visible')):
                err = exc.ElementNotVisible(
                    "Element was not visible when expected during playback. If "
                    "your playback depended on a significant rerender having been "
                    "done, then make sure you've waited until nothing is changing "
                    "before taking a screenshot."
                )
            else:
                err = exception

    output('%s' % str(state))
    if err:
        output(': %s' % str(err))
    return (state, err)

