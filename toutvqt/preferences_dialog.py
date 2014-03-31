from PyQt4 import Qt
from PyQt4 import QtCore
from PyQt4 import QtGui
from toutvqt import utils


class QTouTvPreferencesDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'preferences_dialog'
    settings_accepted = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self._setup_ui()
        self._setup_signals()

    def _setup_signals(self):
        self.accepted.connect(self._send_settings_accepted)

    def _setup_ui(self):
        self._load_ui(QTouTvPreferencesDialog._UI_NAME)
        open_dl_dir_slot = self._open_download_directory_browser
        self.download_directory_browse.clicked.connect(open_dl_dir_slot)

    def _open_download_directory_browser(self, checked):
        msg = 'Select download directory'
        dl_dir = QtGui.QFileDialog.getExistingDirectory(self, msg)
        self.download_directory_value.setText(dl_dir)

    def _send_settings_accepted(self):
        settings = {}

        settings['network/http_proxy'] = self.http_proxy_value.text()
        dl_dir_value = self.download_directory_value.text()
        settings['files/download_directory'] = dl_dir_value

        self.settings_accepted.emit(settings)

    def update_settings_item(self, key, value):
        if key == 'network/http_proxy':
            self.http_proxy_value.setText(value)
        elif key == 'files/download_directory':
            self.download_directory_value.setText(value)
