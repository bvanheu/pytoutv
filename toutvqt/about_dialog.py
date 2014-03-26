from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt


class QTouTvAboutDialog(Qt.QDialog):
    UI_PATH = resource_filename(__name__, 'dat/ui/about_dialog.ui')

    def __init__(self):
        super(QTouTvAboutDialog, self).__init__()

        self._setup_ui()
        #self._setup_signals()

    def _setup_signals(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_ui(self):
        uic.loadUi(QTouTvAboutDialog.UI_PATH, baseinstance=self)

    def show_move(self, pos):
        self.move(pos)
        self.exec()
