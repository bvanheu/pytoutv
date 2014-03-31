from PyQt4 import Qt
from toutvqt import utils


class QTouTvAboutDialog(Qt.QDialog):
    _UI_NAME = 'about_dialog'

    def __init__(self):
        super(QTouTvAboutDialog, self).__init__()

        self._setup_ui()

    def _setup_ui(self):
        utils.load_qt_ui(QTouTvAboutDialog._UI_NAME, self)

    def show_move(self, pos):
        self.move(pos)
        self.exec()
