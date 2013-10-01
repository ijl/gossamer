"""
Objects representing steps a user can take, e.g., make a click,
take a screenshot.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import os
import time

from collections import namedtuple
from selenium.webdriver.support import ui

from gossamer.constant import modes
from gossamer.exc import ScreenshotsDiffer
from gossamer.image import images_identical, image_diff, allowance
from gossamer import util


class TestStep(object): # pylint: disable=R0903
    """
    Base class of test actions, not useful in itself.
    """

    def __init__(self, offset_time):
        self.offset_time = offset_time

    def delayer(self, driver): # pylint: disable=R0201,W0613
        """
        Do not execute until...
        """
        time.sleep(0.25)

    def execute(self, driver, settings, mode):
        """
        Called during :func:`.run.playback` or :func:`.run.rerecord`.
        """
        raise NotImplementedError

    def __json__(self):
        return {self.__class__.__name__: self.__dict__}


class FindElementMixin(object): # pylint: disable=R0903
    """
    driver method lookup for identifier_type.
    """

    _find_element_funcs = {
        'id': 'find_element_by_id',
        'classname': 'find_element_by_class_name',
        'classlist': 'find_element_by_css_selector'
    }


class ElementIdentifierMixin(object): # pylint: disable=R0903
    """
    For steps that need to identify elements and their values.
    """
    identifier = None
    identifier_type = None
    value = None

    eid = None
    ecn = None
    ecl = None
    eid_val = None
    ecn_val = None
    ecl_val = None

    def _process_identifiers_and_values(self):
        """
        Resolve element data to `identifier`, `identifier_type`, and
        `value`.
        """
        # element.id
        self.eid = self.eid if self.eid and len(self.eid) > 0 else None
        # element.className
        self.ecn = self.ecn if self.ecn and len(self.ecn) > 0 else None
        # element.classList
        self.ecl = '.%s' % '. '.join(self.ecl) if self.ecl and len(self.ecl) > 0 else None

        if not (self.eid or self.ecn or self.ecl):
            raise ValueError()
        if self.eid:
            self.identifier = self.eid
            self.identifier_type = 'id'
            self.value = self.eid_val
        elif self.ecl:
            self.identifier = self.ecl
            self.identifier_type = 'classlist'
            self.value = self.ecl_val
        elif self.ecn:
            self.identifier = self.ecn
            self.identifier_type = 'classname'
            self.value = self.ecn_val

        del self.eid
        del self.ecn
        del self.ecl
        del self.eid_val
        del self.ecn_val
        del self.ecl_val


class Navigate(TestStep): # pylint: disable=R0903
    """
    Navigation to a new page.
    """
    playback = True

    def __init__(self, offset_time, url):
        super(Navigate, self).__init__(offset_time)
        self.url = url

    def execute(self, driver, settings, mode):
        from gossamer.run import navigate, wait_until_loaded
        util.log.debug('Navigating to %s', self.url)
        navigate(driver, (self.url, None))
        wait_until_loaded(driver)


ClickParams = namedtuple('ClickParams', ['pos', 'select', 'eid', 'ecn', 'ecl'])


class Click(TestStep): # pylint: disable=R0903
    """
    Click action by the user.
    """

    playback = True

    def __init__(self, offset_time, pos):
        super(Click, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings, mode):
        util.log.debug("Clicking %s", self.pos)
        # Work around multiple bugs in WebDriver's implementation of click()
        driver.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos.x, self.pos.y)
        )


class Dropdown(TestStep, FindElementMixin, ElementIdentifierMixin): # pylint: disable=R0902
    """
    Selecting a dropdown value by the user.
    """

    playback = True

    def __init__(self, offset_time, pos=None,
        eid=[None, None], ecn=[None, None], ecl=[None, None],
        identifier=None, identifier_type=None, value=None
        ): # pylint: disable=R0913
        super(Dropdown, self).__init__(offset_time)
        self.pos = pos

        self.identifier = identifier
        self.identifier_type = identifier_type
        self.value = value

        self.eid = eid[0]
        self.eid_val = eid[1]
        self.ecn = ecn[0]
        self.ecn_val = ecn[1]
        self.ecl = ecl[0]
        self.ecl_val = ecl[1]

        # this is because we don't use a separate step for a processed
        # Dropdown. todo.
        if not (identifier and identifier_type and value):
            self._process_identifiers_and_values()

    def execute(self, driver, settings, mode):
        util.log.debug(
            "Selecting '%s' into '%s' by %s",
            self.value, self.identifier, self.identifier_type
        )
        ui.Select(
            getattr(driver, self._find_element_funcs[self.identifier_type])(self.identifier)
        ).select_by_visible_text(self.value)


KeyParams = namedtuple('KeyParams', ['key', 'shift', 'eid', 'ecn', 'ecl'])


class Key(TestStep, FindElementMixin, ElementIdentifierMixin): # pylint: disable=R0903,R0902,W0223
    """
    Typing action by the user.
    """

    playback = False

    def __init__(self, offset_time, key, shift=None,
        eid=None, ecn=None, ecl=None, eid_val=None, ecn_val=None, ecl_val=None
        ): # pylint: disable=R0913
        super(Key, self).__init__(offset_time)
        self.key = key
        self.shift = shift
        self.identifier = None
        self.identifier_type = None
        self.value = None

        self.eid = eid
        self.ecn = ecn
        self.ecl = ecl
        self.eid_val = eid_val
        self.ecn_val = ecn_val
        self.ecl_val = ecl_val

        self._process_identifiers_and_values()


class Text(TestStep, FindElementMixin): # pylint: disable=R0903
    """
    Text input, after being resolved from Keys.
    """

    playback = True

    def __init__(self, offset_time, identifier, identifier_type, value):
        super(Text, self).__init__(offset_time)
        self.identifier = identifier
        self.identifier_type = identifier_type
        self.value = value

    def delayer(self, driver):
        """
        Do not execute until...
        """
        time.sleep(1)

    def execute(self, driver, settings, mode):
        util.log.debug(
            "Text '%s' into element '%s' by %s",
            self.value, self.identifier, self.identifier_type
        )
        getattr(driver, self._find_element_funcs[self.identifier_type])\
            (self.identifier).send_keys(self.value)


class Screenshot(TestStep):
    """
    Screenshot taken by the user.
    """

    playback = True

    def __init__(self, offset_time, num):
        super(Screenshot, self).__init__(offset_time)
        self.num = num

    def delayer(self, driver):
        """
        Do not execute until...
        """
        time.sleep(1)

    def get_path(self, settings):
        """
        Path to screenshot.
        """
        return os.path.join(settings.path, 'screenshot' + str(self.num) + '.png')

    def execute(self, driver, settings, mode):
        util.log.debug("Taking screenshot %s", self.num)
        original = self.get_path(settings)
        new = os.path.join(settings.path, 'last', 'screenshot%s.png' % self.num)
        if mode in (modes.RECORD, modes.RERECORD):
            driver.save_screenshot(original)
        else:
            driver.save_screenshot(new)
            if not images_identical(original, new, allowance(settings.browser)):
                if settings.save_diff:
                    diffpath = os.path.join(settings.path, 'diff.png')
                    diff = image_diff(original, new, diffpath, settings.diffcolor)
                    raise ScreenshotsDiffer(
                        'Screenshot %s was different; compare %s with %s. See %s '
                        'for the comparison. diff=%r' % (
                            self.num, original, new, diffpath, diff
                        )
                    )
                else:
                    raise ScreenshotsDiffer('Screenshot %s was different.' % self.num)


class Scroll(TestStep): # pylint: disable=R0903
    """
    Scrolling action on the page.
    """

    playback = True

    def __init__(self, offset_time, pos):
        super(Scroll, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings, mode):
        util.log.debug("Scrolling to %s", self.pos)
        driver.execute_script("window.scrollBy(%s, %s)" % (self.pos.x, self.pos.y))

