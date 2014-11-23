from toutvqt import config
from toutvqt import utils
from toutvqt import __version__


class QTouTvAboutDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'about_dialog'

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _set_version(self):
        self.version_label.setText('v{}'.format(__version__))

    @staticmethod
    def _create_list(alist):
        return '\n'.join(alist)

    def _set_contributors(self):
        contributors = QTouTvAboutDialog._create_list(config.CONTRIBUTORS)
        self.contributors_edit.setPlainText(contributors)

    def _set_contents(self):
        self._set_version()
        self._set_contributors()

    def _setup_ui(self):
        self._load_ui(QTouTvAboutDialog._UI_NAME)
        self._set_contents()
        self.adjustSize()
        self.setFixedWidth(self.width())
        self.setFixedHeight(self.height())
