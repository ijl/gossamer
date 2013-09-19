"""
Non-step data structures.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0


class Test(object): # pylint: disable=R0903
    """
    Object to be passed into dispatch... containing all information
    to run (and repeat, if persisted) a test.
    """

    def __init__(self, version, settings, steps):
        self.version = version
        self.settings = settings
        self.steps = steps
    def __json__(self):
        return {
            self.settings.name: {
                'version': self.version,
                'settings': self.settings,
                'steps': self.steps,
            }
        }

    def __repr__(self): # pragma: no cover
        return "<%s %r>" % (
            self.__class__.__name__,
            self.settings.name
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
        Return data in form expected by :func:`gossamer.run.navigate`.
        """
        return (self.url, self.postdata)

    def __json__(self):
        return self.__dict__

    def __repr__(self): # pragma: no cover
        return '<%s %r>' % (self.__class__.__name__, self.__dict__)


class Point(object): # pylint: disable=R0903
    """
    Contains validated x, y coordinates for screen position.
    """

    def __init__(self, x, y):
        """
        Stores x and y coordinates. They cannot be negative.
        """
        if x < 0 or y < 0: # pragma: no cover
            raise ValueError(
                'Coordinates [%s, %s] cannot be negative' % (x, y)
            )
        self.x = x
        self.y = y

    def __json__(self):
        return self.__dict__

    def __repr__(self): # pragma: no cover
        return '<Point %s, %s>' % (self.x, self.y)
