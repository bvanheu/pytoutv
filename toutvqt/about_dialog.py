from PyQt4 import Qt
from toutvqt import utils


class QTouTvAboutDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'about_dialog'

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        self._load_ui(QTouTvAboutDialog._UI_NAME)
