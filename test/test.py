"""
Smoke tests. Needs to be improved.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest
from huxley import util
import json
import pkg_resources
import os


class TestUtilities(unittest.TestCase): # pylint: disable=R0904
    """
    Utilities
    """

    def setUp(self):
        super(TestUtilities, self).setUp()
        self.data = json.loads(
            pkg_resources.resource_stream('test', 'test_data.json').read()
        )

    def test_read_run(self): # pylint: disable=R0201
        """
        util.import_recorded_run
        """
        util.import_recorded_run(self.data)

    def test_write_run(self):
        """
        util.write_recorded_run
        """
        try:
            filename = '/tmp'
            util.write_recorded_run(filename, util.import_recorded_run(self.data))
        finally:
            os.unlink(os.path.join(filename, 'record.json'))
