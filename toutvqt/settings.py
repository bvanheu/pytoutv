from PyQt4.Qt import QDir
from PyQt4.Qt import QSettings
from PyQt4 import QtCore
from PyQt4 import Qt
import logging


class QTouTvSettings(Qt.QObject):
    _DEFAULT_DOWNLOAD_DIRECTORY = QDir.home().absoluteFilePath('TOU.TV Downloads')
    setting_item_changed = QtCore.pyqtSignal(str, object)

    def __init__(self):
        super(QTouTvSettings, self).__init__()
        self._fill_defaults()
        self._settings_dict = {}
        self.setting_item_changed.connect(self.tmp)

    def _fill_defaults(self):
        """Fills defaults with sensible default values."""
        self.defaults = {}
        def_dl_dir = QTouTvSettings._DEFAULT_DOWNLOAD_DIRECTORY
        self.defaults['files/download_directory'] = def_dl_dir
        self.defaults['network/http_proxy'] = None

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

    def apply_settings(self, new_settings):
        for key in new_settings:
            new_value = new_settings[key]
            if key in self._settings_dict:
                if new_value != self._settings_dict[key]:
                    # Value changed
                    self.setting_item_changed.emit(key, new_value)
            else:
                # New setting key
                self.setting_item_changed.emit(key, new_value)
            self._settings_dict[key] = new_settings[key]

        self.write_settings()

    def debug_print_settings(self):
        print(self._settings_dict)

    def tmp(self, k, v):
        print("%s changed to %s" % (k, v))
