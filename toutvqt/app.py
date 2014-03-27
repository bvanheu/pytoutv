import sys
import platform
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow

from toutv import client


class QTouTvApp(Qt.QApplication):
    def __init__(self, args):
        super(QTouTvApp, self).__init__(args)

        self._setup_client()
        self._start()

    def _start(self):
        self.main_window = QTouTvMainWindow(self, self.client)
        self.main_window.show()

    def _setup_client(self):
        self.client = client.Client()


def _register_sigint():
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = QTouTvApp(sys.argv)
    _register_sigint()

    return app.exec_()
