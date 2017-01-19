import glob
import os
import unittest

from toutvcli import app


run_these_tests = 'PYTOUTV_RUN_REAL_TESTS' in os.environ


@unittest.skipIf(not run_these_tests,
                 "skippiing tests against real service")
class ToutvCliAppRealTest(unittest.TestCase):
    """Tou.TV command line tool tests against the real service.

    These tests are testing the Tou.TV CLI tool against the real Tou.TV
    service.  They might not work everywhere, since a lot of content is
    restricted geographically.  Also, because the content might change over
    time, so the tests may become invalid.  For these reasons, they are skipped
    by default.  If you want to run them, define the PYTOUTV_RUN_REAL_TESTS
    environment variable while running the tests.  For example:

      $ PYTOUTV_RUN_REAL_TESTS=1 pytest test_app_real.py
    """

    def _testInfo(self, args):
        args = ['--verbose', 'info'] + args

        self.assertEqual(app.App(args).run(), 0)

    def testInfo(self):
        self._testInfo(['Le show caché 2'])
        self._testInfo(['Infoman'])
        self._testInfo(['http://ici.tou.tv/infoman'])
        self._testInfo(['Infoman', 'S17E12'])
        self._testInfo(['http://ici.tou.tv/infoman/S17E12?lectureauto=1'])

    def _testList(self, args):
        args = ['--verbose', 'list'] + args

        self.assertEqual(app.App(args).run(), 0)

    def testList(self):
        self._testList([])
        self._testList(['Le show caché 2'])
        self._testList(['Infoman'])
        self._testList(['http://ici.tou.tv/infoman'])

    def _testSearch(self, args):
        args = ['--verbose', 'search'] + args

        self.assertEqual(app.App(args).run(), 0)

    def testSearch(self):
        self._testSearch(['Le show caché 2'])
        self._testSearch(['Infoman'])

    def _testFetch(self, expected_filename, args):
        # Delete the file if it exists prior to the test.
        for file in glob.glob(expected_filename):
            os.unlink(file)

        args = ['--verbose', 'fetch', '-qMIN'] + args

        self.assertEqual(app.App(args).run(), 0)

        self.assertTrue(len(glob.glob(expected_filename)) > 0)

        # Be nice and leave no trace.
        for file in glob.glob(expected_filename):
            os.unlink(file)

    def testFetch(self):
        self._testFetch('Coup.de.pouce.*.S2012E01.*.01.qMIN.ts',
                        ['COUP DE POUCE POUR LA PLANÈTE', 'S2012E01'])
