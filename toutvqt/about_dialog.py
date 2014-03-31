from PyQt4 import Qt
from toutvqt import utils
from toutvqt import __version__


class QTouTvAboutDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'about_dialog'

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _set_version(self):
        self.version_label.setText('v{}'.format(__version__))

    def _setup_ui(self):
        self._load_ui(QTouTvAboutDialog._UI_NAME)
        self._set_version()
