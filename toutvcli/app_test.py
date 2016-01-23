import os
import unittest

from toutvcli import app

class ToutvCliAppTest(unittest.TestCase):
    def testApp(self):
        filename = 'Les.astres.noirs.S2009E01.Les.astres.noirs.460kbps.ts'
        expected_size = 58212288
        args = ['fetch', '-f', '-q', 'MIN', 'Les astres noirs', 'S2009E01']
        a = app.App(args)
        rc = a.run()
        self.assertEquals(rc, 0)
        self.assertTrue(os.path.exists(filename))
        self.assertEquals(os.path.getsize(filename), expected_size)
