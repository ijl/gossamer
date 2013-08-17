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

class TestStep(object):
    def __init__(self, offset_time):
        self.offset_time = offset_time

    def execute(self, driver, settings):
        raise NotImplementedError


class ClickTestStep(TestStep):
    CLICK_ID = '_huxleyClick'

    def __init__(self, offset_time, pos):
        super(ClickTestStep, self).__init__(offset_time)
        self.pos = pos

    def execute(self, driver, settings):
        print '  Clicking', self.pos
        # Work around multiple bugs in WebDriver's implementation of click()
        driver.execute_script(
            'document.elementFromPoint(%d, %d).click();' % (self.pos.x, self.pos.y)
        )


class KeyTestStep(TestStep):
    KEY_ID = '_huxleyKey'

    def __init__(self, offset_time, key):
        super(KeyTestStep, self).__init__(offset_time)
        self.key = key

    def execute(self, driver, settings):
        print '  Typing', self.key
        eid = driver.execute_script('return document.activeElement.id;')
        if eid is None or eid == '':
            driver.execute_script(
                'document.activeElement.id = %r;' % self.KEY_ID
            )
            eid = self.KEY_ID
        driver.find_element_by_id(eid).send_keys(self.key.lower())


class ScreenshotTestStep(TestStep):
    def __init__(self, offset_time, index):
        super(ScreenshotTestStep, self).__init__(offset_time)
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
                            ('Screenshot %s was different; compare %s with %s. See %s ' +
                             'for the comparison. diff=%r') % (
                                self.index, original, new, diffpath, diff
                            )
                        )
                    else:
                        raise TestError('Screenshot %s was different.' % self.index)
            finally:
                if not settings.save_diff:
                    os.unlink(new)
