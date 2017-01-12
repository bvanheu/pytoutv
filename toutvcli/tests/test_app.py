import unittest

from toutvcli import app


class ToutvCliAppTest(unittest.TestCase):

    def setUp(self):
        self._app = app.App([])

    def _testArgParsing(self, first, second, exp_first, exp_second):
        act_first, act_second = self._app._parse_show_episode_from_args(first, second)
        self.assertEqual(act_first, exp_first)
        self.assertEqual(act_second, exp_second)

    def _testArgParsingRaises(self, first, second):
        with self.assertRaises(app.CliError):
            self._app._parse_show_episode_from_args(first, second)

    def testArgParsing(self):
        self._testArgParsing('http://ici.tou.tv/infoman', None,
                             'infoman', None)
        self._testArgParsing('http://ici.tou.tv/infoman/S17E12?lectureauto=1', None,
                             'infoman', 'S17E12')
        self._testArgParsing('infoman', 'S17E12',
                             'infoman', 'S17E12')

        # Wrong domain
        self._testArgParsingRaises('http://www.perdu.com/', None)

        # Extra argument after URL
        self._testArgParsingRaises('http://ici.tou.tv/infoman', 'S17E12')

        # Wrong URL formats
        self._testArgParsingRaises('http://ici.tou.tv/infoman/S17E12/something', None)
        self._testArgParsingRaises('http://ici.tou.tv/', None)

    def testInfo(self):
        self.assertEqual(app.App(['--verbose', 'info', 'Le show caché 2']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'info', 'Infoman']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'info', 'http://ici.tou.tv/infoman']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'info', 'Infoman', 'S17E12']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'info', 'http://ici.tou.tv/infoman/S17E12?lectureauto=1']).run(), 0)

    def testList(self):
        self.assertEqual(app.App(['--verbose', 'list', 'Le show caché 2']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'list', 'Infoman']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'list', 'http://ici.tou.tv/infoman']).run(), 0)

    def testSearch(self):
        self.assertEqual(app.App(['--verbose', 'search', 'Le show caché 2']).run(), 0)
        self.assertEqual(app.App(['--verbose', 'search', 'Infoman']).run(), 0)

