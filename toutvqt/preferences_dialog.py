from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt


class QTouTvPreferencesDialog(Qt.QDialog):
    UI_PATH = resource_filename(__name__, 'dat/ui/preferences_dialog.ui')

    def __init__(self):
        super(QTouTvPreferencesDialog, self).__init__()

        self._setup_ui()
        #self._setup_signals()

    def _setup_signals(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_ui(self):
        uic.loadUi(QTouTvPreferencesDialog.UI_PATH, baseinstance=self)

    def show_move(self, pos):
        self.move(pos)
        self.exec()
