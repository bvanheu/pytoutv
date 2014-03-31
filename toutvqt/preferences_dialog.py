from PyQt4 import Qt
from PyQt4 import QtCore
from PyQt4 import QtGui
from toutvqt import utils


class QTouTvPreferencesDialog(Qt.QDialog):
    _UI_NAME = 'preferences_dialog'
    config_accepted = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(QTouTvPreferencesDialog, self).__init__()

        self._setup_ui()
        self._setup_signals()

    def _setup_signals(self):
        self.accepted.connect(self._send_config_accepted)

    def _setup_ui(self):
        utils.load_qt_ui(QTouTvPreferencesDialog._UI_NAME, self)
        open_dl_dir_slot = self._open_download_directory_browser
        self.download_directory_browse.clicked.connect(open_dl_dir_slot)

    def _open_download_directory_browser(self, checked):
        msg = 'Select download directory'
        dl_dir = QtGui.QFileDialog.getExistingDirectory(self, msg)
        self.download_directory_value.setText(dl_dir)

    def show_move(self, pos):
        self.move(pos)
        self.exec()

    def _send_config_accepted(self):
        config = {}

        config['network/http_proxy'] = self.http_proxy_value.text()
        dl_dir_value = self.download_directory_value.text()
        config['files/download_directory'] = dl_dir_value

        self.config_accepted.emit(config)

    def update_config_item(self, key, value):
        if key == 'network/http_proxy':
            self.http_proxy_value.setText(value)
        elif key == 'files/download_directory':
            self.download_directory_value.setText(value)
