import os.path
from PyQt4.Qt import QDir
from PyQt4.Qt import QSettings
from PyQt4 import QtCore
from PyQt4 import Qt
import logging


class SettingsKeys:
    FILES_DOWNLOAD_DIR = 'files/download_directory'
    NETWORK_HTTP_PROXY = 'network/http_proxy'


class QTouTvSettings(Qt.QObject):
    _DEFAULT_DOWNLOAD_DIRECTORY = QDir.home().absoluteFilePath('TOU.TV Downloads')
    setting_item_changed = QtCore.pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._fill_defaults()
        self._settings_dict = {}

    def _fill_defaults(self):
        """Fills defaults with sensible default values."""
        self.defaults = {}
        def_dl_dir = QTouTvSettings._DEFAULT_DOWNLOAD_DIRECTORY
        self.defaults[SettingsKeys.FILES_DOWNLOAD_DIR] = def_dl_dir
        self.defaults[SettingsKeys.NETWORK_HTTP_PROXY] = ""

    def write_settings(self):
        logging.debug('Writing settings')

        settings = QSettings()
        settings.clear()

        for k in self._settings_dict:
            if k in self.defaults:
                if self._settings_dict[k] != self.defaults[k]:
                    settings.setValue(k, self._settings_dict[k])
            else:
                msg = 'Setting key {} not found in defaults'.format(k)
                logging.warning(msg)
                settings.setValue(k, self._settings_dict[k])

    def read_settings(self):
        logging.debug('Reading settings')

        settings = QSettings()
        read_settings = self.defaults.copy()
        keys = settings.allKeys()

        for k in keys:
            read_settings[k] = settings.value(k)

        self.apply_settings(read_settings)

    def _apply_settings(self, key, new_value):
        """Apply the new value. Return whether the value changed."""

        # If the key did not exist, it "changed".
        if key not in self._settings_dict:
            self._settings_dict[key] = new_value
            return True

        cur_value = self._settings_dict[key]
        if cur_value == new_value:
            return False

        self._settings_dict[key] = new_value

        return True

    def apply_settings(self, new_settings):
        logging.debug('Applying settings')

        for key in new_settings:
            new_value = new_settings[key]
            if self._apply_settings(key, new_value):
                self.setting_item_changed.emit(key, new_value)

        self.write_settings()

    def get_download_directory(self):
        return self._settings_dict[SettingsKeys.FILES_DOWNLOAD_DIR]

    def get_http_proxy(self):
        return self._settings_dict[SettingsKeys.NETWORK_HTTP_PROXY]

    def debug_print_settings(self):
        print(self._settings_dict)
