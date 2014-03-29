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

        self.setOrganizationName("src")
        self.setApplicationName("toutv")

        self._setup_client()
        self._setup_ui()
        self._setup_config()
        self._start()

    def _start(self):
        self.main_window.start()

    def _setup_ui(self):
        self.main_window = QTouTvMainWindow(self, self._client)

    def _setup_client(self):
        self._client = client.Client()

    def _setup_config(self):
        # Create a default config
        self._config = QTouTvConfig()

        # Connect the signals between the config and preferences dialog
        preferences_dialog = self.main_window.preferences_dialog
        config_item_changed = self._config.config_item_changed
        preferences_dialog.config_accepted.connect(self._config.apply_config)
        config_item_changed.connect(preferences_dialog.update_config_item)
        self._config.config_item_changed.connect(self._config_item_changed)

        # Read the settings from disk
        self._config.read_settings()

    def _config_item_changed(self, key, value):
        if key == 'network/http_proxy':
            self._client.transport.set_http_proxy(value)


def _register_sigint():
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = QTouTvApp(sys.argv)
    _register_sigint()

    return app.exec_()
