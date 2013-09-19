"""
Smoke tests. Needs to be improved.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import unittest
from gossamer import util, run, integration
import json
import pkg_resources
import os
import shutil


class TestUtilities(unittest.TestCase): # pylint: disable=R0904
    """
    Utilities
    """

    def setUp(self):
        super(TestUtilities, self).setUp()
        self.data = json.loads(
            pkg_resources.resource_stream('test', 'data/record.json').read()
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


class TestRun(unittest.TestCase): # pylint: disable=R0904
    """
    Run
    """

    def test_has_page_changed(self):
        """
        run._has_page_changed
        """
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/', 'http://www.example.com/'
            ), False
        )
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/', 'http://www.example.com'
            ), False
        )
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/page1', 'http://www.example.com/page2'
            ), True
        )
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/page1', 'http://www.example.com/page2'
            ), True
        )
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/page1', 'http://www.example.com/page1?q=query'
            ), True
        )
        self.assertEqual(run._has_page_changed( # pylint: disable=W0212
            'http://www.example.com/#/page1', 'http://www.example.com/#/page2'
            ), False
        )

class TestIntegration(unittest.TestCase): # pylint: disable=R0904
    """
    Integration
    """

    def test_run_gossamerfile(self):
        """
        integration.run_gossamerfile
        """
        test_dir = os.path.join(os.getcwd(), 'test', 'data')
        gossamerfile = os.path.join(test_dir, 'Gossamerfile')
        try:
            tests = ['example', 'mdn']
            for test in tests:
                dirname = os.path.join('/tmp/', test)
                shutil.copytree(os.path.join(test_dir, test), dirname)
            integration.run_gossamerfile(
                locals(),
                gossamerfile,
                '/tmp',
                browser='chrome'
            )
            self.assertTrue('GossamerTest_example' in locals())
            self.assertTrue('GossamerTest_mdn' in locals())
            for cls in (locals()['GossamerTest_example'], locals()['GossamerTest_mdn']):
                self.assertTrue(cls == integration.GossamerTestCase)
        finally:
            try:
                shutil.rmtree('/tmp/example')
                shutil.rmtree('/tmp/mdn')
            except OSError:
                pass
