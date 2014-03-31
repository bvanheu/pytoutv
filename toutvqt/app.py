import os
import sys
import platform
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow
from toutvqt.settings import QTouTvSettings
from toutvqt import config
import toutv.client



class _QTouTvApp(Qt.QApplication):
    def __init__(self, args):
        super(_QTouTvApp, self).__init__(args)

        self.setOrganizationName(config.ORG_NAME)
        self.setApplicationName(config.APP_NAME)

        self._setup_client()
        self._setup_ui()
        self._setup_settings()
        self._start()

    def _start(self):
        self.main_window.start()

    def _setup_ui(self):
        self.main_window = QTouTvMainWindow(self, self._client)

    def _setup_client(self):
        self._client = toutv.client.Client()

    def _setup_settings(self):
        # Create a default settings
        self._settings = QTouTvSettings()

        # Connect the signals between the settings and preferences dialog
        preferences_dialog = self.main_window.preferences_dialog
        setting_item_changed = self._settings.setting_item_changed
        preferences_dialog.settings_accepted.connect(self._settings.apply_settings)
        setting_item_changed.connect(preferences_dialog.update_settings_item)
        self._settings.setting_item_changed.connect(self._setting_item_changed)

        # Read the settings from disk
        self._settings.read_settings()

    def _on_setting_http_proxy_changed(self, value):
        self._client.set_transport_http_proxy(value)

    def _on_setting_dl_dir_changed(self, value):
        # Create output directory if it doesn't exist
        if not os.path.exists(value):
            try:
                os.makedirs(value)
            except:
                # Ignore; should fail later
                pass

    def _setting_item_changed(self, key, value):
        if key == 'network/http_proxy':
            self._on_setting_http_proxy_changed(value)
        elif key == 'files/download_directory':
            self._on_setting_dl_dir_changed(value)


def _register_sigint():
    if platform.system() == 'Linux':
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = _QTouTvApp(sys.argv)
    _register_sigint()

    return app.exec_()
