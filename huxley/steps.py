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

"""
Objects representing steps a user can take, e.g., make a click,
take a screenshot.
"""

import os, time

from huxley.consts import modes
from huxley.errors import TestError
from huxley.images import images_identical, image_diff
from huxley import util


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


class TestStep(object): # pylint: disable=R0903
    """
    Base class of test actions, not useful in itself.
    """

    def __init__(self, offset_time):
        self.delayer = None
        self.offset_time = offset_time

    def execute(self, driver, settings):
        raise NotImplementedError


class Click(TestStep): # pylint: disable=R0903
    """
    Click action by the user.
    """

    playback = True

    def __init__(self, offset_time, pos):
        super(Click, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings):
        util.log.debug("Clicking %s", self.pos)
        # Work around multiple bugs in WebDriver's implementation of click()
        driver.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos.x, self.pos.y)
        )


class Key(TestStep): # pylint: disable=R0903
    """
    Typing action by the user.
    """

    playback = False

    def __init__(self, offset_time, key, shift=None,
        eid=None, ecn=None, ecl=None, eid_val=None, ecn_val=None, ecl_val=None
        ):
        super(Key, self).__init__(offset_time)
        self.key = key
        self.shift = shift
        self.identifier = None
        self.identifier_type = None
        self.value = None

        # element.id
        self.eid = eid if eid and len(eid) > 0 else None
        # element.className
        self.ecn = ecn if ecn and len(ecn) > 0 else None
        # element.classList
        self.ecl = '.%s' % '. '.join(ecl) if ecl and len(ecl) > 0 else None

        self.eid_val = eid_val
        self.ecn_val = ecn_val
        self.ecl_val = ecl_val

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


class Text(TestStep): # pylint: disable=R0903

    playback = True

    def __init__(self, offset_time, identifier, identifier_type, value):
        super(Text, self).__init__(offset_time)
        self.identifier = identifier
        self.identifier_type = identifier_type
        self.value = value

    def execute(self, driver, settings):
        util.log.debug(
            "Text '%s' into element '%s' by %s",
            self.value, self.identifier, self.identifier_type
        )
        funcs = {
            'id': driver.find_element_by_id,
            'classname': driver.find_element_by_class_name,
            'classlist': driver.find_element_by_css_selector
        }
        funcs[self.identifier_type](self.identifier).send_keys(self.value)


class Screenshot(TestStep):
    """
    Screenshot taken by the user.
    """

    playback = True

    def __init__(self, offset_time, index):
        super(Screenshot, self).__init__(offset_time)
        self.index = index

    def get_path(self, settings):
        return os.path.join(settings.path, 'screenshot' + str(self.index) + '.png')

    def execute(self, driver, settings):
        util.log.debug("Taking screenshot %s", self.index)
        original = self.get_path(settings)
        new = os.path.join(settings.path, 'last', 'screenshot%s.png' % self.index)
        if settings.mode == modes.RERECORD:
            driver.save_screenshot(original)
        else:
            driver.save_screenshot(new)
            if not images_identical(original, new):
                if settings.save_diff:
                    diffpath = os.path.join(settings.path, 'diff.png')
                    diff = image_diff(original, new, diffpath, settings.diffcolor)
                    raise TestError(
                        'Screenshot %s was different; compare %s with %s. See %s '
                        'for the comparison. diff=%r' % (
                            self.index, original, new, diffpath, diff
                        )
                    )
                else:
                    raise TestError('Screenshot %s was different.' % self.index)


class Scroll(TestStep):
    """
    Scrolling action on the page.
    """

    def __init__(self, offset_time, pos):
        super(Scroll, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings):
        util.log.debug("Scrolling to %s", self.pos)
        driver.execute_script("window.scrollBy(%s, %s)" % (self.pos.x, self.pos.y))

