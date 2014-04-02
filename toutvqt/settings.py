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
        self.setting_item_changed.connect(self.tmp)

    def _fill_defaults(self):
        """Fills defaults with sensible default values."""
        self.defaults = {}
        def_dl_dir = QTouTvSettings._DEFAULT_DOWNLOAD_DIRECTORY
        self.defaults[SettingsKeys.FILES_DOWNLOAD_DIR] = def_dl_dir
        self.defaults[SettingsKeys.NETWORK_HTTP_PROXY] = None

    def write_settings(self):
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
        settings = QSettings()
        read_settings = self.defaults.copy()
        keys = settings.allKeys()

        for k in keys:
            read_settings[k] = settings.value(k)

        self.apply_settings(read_settings)

    def _change_setting(self, key, value):
        if key == SettingsKeys.FILES_DOWNLOAD_DIR:
            new_value = os.path.abspath(value)
            if new_value == value:
                return False

            self._settings_dict[key] = new_value

        return True

    def apply_settings(self, new_settings):
        for key in new_settings:
            new_value = new_settings[key]
            if key in self._settings_dict:
                if new_value != self._settings_dict[key]:
                    # Value changed
                    if self._change_setting(key, new_value):
                        value = self._settings_dict[key]
                        self.setting_item_changed.emit(key, value)
            else:
                # New setting key
                self.setting_item_changed.emit(key, new_value)
            self._settings_dict[key] = new_settings[key]

        self.write_settings()

    def get_download_directory(self):
        return self._settings_dict[SettingsKeys.FILES_DOWNLOAD_DIR]

    def get_http_proxy(self):
        return self._settings_dict[SettingsKeys.NETWORK_HTTP_PROXY]

    def debug_print_settings(self):
        print(self._settings_dict)

    def tmp(self, k, v):
        print("%s changed to %s" % (k, v))
