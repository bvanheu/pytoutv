import sys
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow


TOUTV_UI_FILE = resource_filename(__name__, 'dat/main_window.ui')


class TouTvQt(Qt.QApplication):
    def __init__(self, args):
        super(TouTvQt, self).__init__(args)

        self._start()

    def _start(self):
        self.main_window = QTouTvMainWindow(self)
        self.main_window.show()


def _register_sigint(app):
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = TouTvQt(sys.argv)

    return app.exec_()
