from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4 import QtCore


class QTouTvPreferencesDialog(Qt.QDialog):
    UI_PATH = resource_filename(__name__, 'dat/ui/preferences_dialog.ui')

    def __init__(self):
        super(QTouTvPreferencesDialog, self).__init__()

        self._setup_ui()
        self._setup_signals()

    config_accepted = QtCore.pyqtSignal(dict)

    def _setup_signals(self):
        self.accepted.connect(self.send_config_accepted)
        # self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_ui(self):
        uic.loadUi(QTouTvPreferencesDialog.UI_PATH, baseinstance=self)

    def show_move(self, pos):
        self.move(pos)
        self.exec()

    def send_config_accepted(self):
        config = {}

        config['network/http_proxy'] = self.http_proxy_value.text()
        config['files/download_directory'] = self.download_directory_value.text()

        self.config_accepted.emit(config)

    def update_config_item(self, key, value):
        if key == 'network/http_proxy':
            self.http_proxy_value.setText(value)
        elif key == 'files/download_directory':
            self.download_directory_value.setText(value)
