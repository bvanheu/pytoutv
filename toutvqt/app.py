import sys
import platform
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow
from toutvqt.config import QTouTvConfig

from toutv import client
from toutv import transport


class QTouTvApp(Qt.QApplication):
    def __init__(self, args):
        super(QTouTvApp, self).__init__(args)

        self._setup_client()
        self._setup_ui()
        self._setup_config()
        self._start()

    def _start(self):
        self.main_window.show()

    def _setup_ui(self):
        self.main_window = QTouTvMainWindow(self, self.client)

    def _setup_client(self):
        tp = transport.JsonTransport(http_proxy = None)
        self.client = client.Client(transport = tp)

    def _setup_config(self):
        # Create a default config
        self.config = QTouTvConfig()

        # Connect the signals between the config and preferences dialog
        self.main_window.preferences_dialog.config_accepted.connect(self.config.apply_config)
        self.config.config_item_changed.connect(self.main_window.preferences_dialog.update_config_item)

        # Read the settings from disk
        self.config.read_settings()

def _register_sigint():
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = QTouTvApp(sys.argv)
    _register_sigint()

    return app.exec_()
