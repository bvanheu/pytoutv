import os
import sys
import logging
import platform
from PyQt4 import Qt
from toutvqt.main_window import QTouTvMainWindow
from toutvqt.settings import QTouTvSettings
from toutvqt.settings import SettingsKeys
from toutvqt import config
import toutv.client


class _QTouTvApp(Qt.QApplication):
    def __init__(self, args):
        super().__init__(args)

        self._proxies = None

        self.setOrganizationName(config.ORG_NAME)
        self.setApplicationName(config.APP_NAME)

        self._setup_client()
        self._setup_settings()
        self._setup_ui()
        self._start()

    def get_settings(self):
        return self._settings

    def get_proxies(self):
        return self._proxies

    def stop(self):
        self.main_window.close()

    def _start(self):
        logging.debug('Starting application')
        self.main_window.start()

    def _setup_ui(self):
        self.main_window = QTouTvMainWindow(self, self._client)

        # Connect the signal between main window and the settings
        self.main_window.settings_accepted.connect(
            self._settings.apply_settings)

    def _setup_client(self):
        self._client = toutv.client.Client()

    def _setup_settings(self):
        # Create a default settings
        self._settings = QTouTvSettings()

        # Connect the signal between settings and us
        self._settings.setting_item_changed.connect(self._setting_item_changed)

        # Read the settings from disk
        self._settings.read_settings()

    def _on_setting_http_proxy_changed(self, value):
        proxies = None
        if value is not None:
            value = value.strip()
            if not value:
                proxies = None
            else:
                proxies = {
                    'http': value,
                    'https': value
                }

        self._proxies = proxies
        self._client.set_proxies(proxies)

    def _on_setting_dl_dir_changed(self, value):
        # Create output directory if it doesn't exist
        if not os.path.exists(value):
            logging.debug('Directory "{}" does not exist'.format(value))
            try:
                os.makedirs(value)
            except Exception:
                # Ignore; should fail later
                logging.warning('Cannot create directory "{}"'.format(value))
                pass

    def _setting_item_changed(self, key, value):
        logging.debug('Setting "{}" changed to "{}"'.format(key, value))
        if key == SettingsKeys.NETWORK_HTTP_PROXY:
            self._on_setting_http_proxy_changed(value)
        elif key == SettingsKeys.FILES_DOWNLOAD_DIR:
            self._on_setting_dl_dir_changed(value)


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            app.stop()

        import signal
        signal.signal(signal.SIGINT, handler)


def _configure_logging():
    fmt = '[thread %(threadName)10s] %(levelname)7s %(asctime)s ' \
          '%(message)s(%(funcName)s@%(filename)s:%(lineno)d)'
    logging.basicConfig(level=logging.WARNING, format=fmt)


def run():
    _configure_logging()
    app = _QTouTvApp(sys.argv)
    _register_sigint(app)

    return app.exec_()


if __name__ == '__main__':
    run()
