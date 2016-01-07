import os
import unittest

from toutvcli import app

class ToutvCliAppTest(unittest.TestCase):
    def testApp(self):
        filename = 'Projet-M.S01E01.Episode.1.560kbps.ts'
        expected_size = 55874560
        args = ['fetch', '-f', '-q', 'MIN', 'Projet-M', 'S01E01']
        a = app.App(args)
        rc = a.run()
        self.assertEquals(rc, 0)
        self.assertTrue(os.path.exists(filename))
        self.assertEquals(os.path.getsize(filename), expected_size)
