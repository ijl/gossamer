"""
Non-step data structures.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0


class Test(object): # pylint: disable=R0903
    """
    Persists a test as `record.json`.
    """

    def __init__(self, browser, screensize, steps=None):
        self.version = 1
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


class TestRun(object):  # pylint: disable=R0903
    """
    Object to be passed into dispatch... containing all information
    to run (and repeat, if persisted) a test.
    """

    def __init__(self, settings, recorded_run=None):
        self.settings = settings
        self.recorded_run = recorded_run

    def __repr__(self):
        return "%s: %r, %r" % (
            self.__class__.__name__,
            self.settings,
            self.recorded_run
        )


class Settings(object): # pylint: disable=R0903,R0902
    """
    Hold validated settings for a specific test run.
    """

    def __init__(self,
            name, url, mode, path, browser,
            screensize, postdata,
            diffcolor, save_diff, cookies=None, desc=None
        ): # pylint: disable=R0913
        self.name = name
        self.url = url
        self.mode = mode
        self.path = path
        self.browser = browser
        self.screensize = screensize
        self.postdata = postdata
        self.diffcolor = diffcolor
        self.save_diff = save_diff
        self.desc = desc
        self.cookies = cookies

    def navigate(self):
        """
        Return data in form expected by :func:`huxley.run.navigate`.
        """
        return (self.url, self.postdata)

    def __repr__(self):
        return '%s: %r' % (self.__class__.__name__, self.__dict__)


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
