import os
import unittest

from toutvcli import app

class ToutvCliAppTest(unittest.TestCase):
    def testApp(self):
        filename = 'Strobosketch.S01E01.Épisode.1.559kbps.ts'
        expected_size = 6888768
        args = ['fetch', '-f', '-q', 'MIN', 'Strobosketch', 'S01E01']
        a = app.App(args)
        rc = a.run()
        self.assertEquals(rc, 0)
        self.assertTrue(os.path.exists(filename))
        self.assertEquals(os.path.getsize(filename), expected_size)
