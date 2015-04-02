import unittest

from toutvcli import app

class ToutvCliAppTest(unittest.TestCase):
    def testApp(self):
        a = app.App(['fetch', '-q', 'MIN', '2327799176', '2303281531'])
        rc = a.run()
        self.assertEquals(rc, 0)
