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

import os

from huxley.consts import modes
from huxley.errors import TestError
from huxley.images import images_identical, image_diff

class Window(object):
    """
    Persist state of the window at a given time... not a step, so todo.
    """

    def __init__(self, offset_time, x, y):
        pass

class TestStep(object): # pylint: disable=R0903
    """
    Base class of test actions, not useful in itself.
    """

    def __init__(self, offset_time):
        self.offset_time = offset_time

    def execute(self, driver, settings):
        raise NotImplementedError


class Click(TestStep): # pylint: disable=R0903
    """
    Click action by the user.
    """

    CLICK_ID = '_huxleyClick'

    def __init__(self, offset_time, pos):
        super(Click, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings):
        print '  Clicking', self.pos
        # Work around multiple bugs in WebDriver's implementation of click()
        driver.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos.x, self.pos.y)
        )


class Key(TestStep): # pylint: disable=R0903
    """
    Typing action by the user.
    """

    KEY_ID = '_huxleyKey'

    def __init__(self, offset_time, key, shift=None, eid=None, ecn=None, ecl=None):
        super(Key, self).__init__(offset_time)
        self.key = key
        self.shift = shift
        self.eid = eid if eid and len(eid) > 0 else None # element.id
        self.ecn = ecn if ecn and len(ecn) > 0 else None # element.className
        self.ecl = ecl if ecl and len(ecl) > 0 else None # element.classList

    def execute(self, driver, settings):
        if self.eid:
            elm = driver.find_element_by_id(self.eid)
        elif self.ecn:
            elm = driver.find_element_by_class_name(self.ecn)
        elif self.ecl:
            elm = driver.find_element_by_class_list(self.ecl)
        elm.send_keys((self.key.lower() if not self.shift else self.key))


class Screenshot(TestStep):
    """
    Screenshot taken by the user.
    """
    
    def __init__(self, offset_time, index):
        super(Screenshot, self).__init__(offset_time)
        self.index = index

    def get_path(self, settings):
        return os.path.join(settings.path, 'screenshot' + str(self.index) + '.png')

    def execute(self, driver, settings):
        print '  Taking screenshot', self.index
        original = self.get_path(settings)
        new = os.path.join(settings.path, 'last.png')
        if settings.mode == modes.RERECORD:
            driver.save_screenshot(original)
        else:
            driver.save_screenshot(new)
            try:
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
            finally:
                if not settings.save_diff:
                    os.unlink(new)


class Scroll(TestStep):
    """
    Scrolling action on the page.
    """

    def __init__(self, offset_time, pos):
        super(Scroll, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings):
        print  "Scrolling,"
        driver.execute_script("window.scrollBy(%s, %s)" % (self.pos.x, self.pos.y))

