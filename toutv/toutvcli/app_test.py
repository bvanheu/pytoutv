import os
import unittest

from toutvcli import app

class ToutvCliAppTest(unittest.TestCase):
    def testApp(self):
        filename = 'Mardi.S2011E01.Mardi.460kbps.ts'
        expected_size = 25836032
        a = app.App(['fetch', '-q', 'MIN', '2327799176', '2303281531'])
        rc = a.run()
        self.assertEquals(rc, 0)
        self.assertTrue(os.path.exists(filename))
        self.assertEquals(os.path.getsize(filename), expected_size)
