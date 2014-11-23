from PyQt4 import Qt
from PyQt4 import QtCore
from toutvqt import utils
from enum import Enum


class SymbolicQuality(Enum):
    LOWEST = 0
    AVERAGE = 1
    HIGHEST = 2


class _QQualityButton(Qt.QPushButton):

    def __init__(self, quality):
        super().__init__()

        self._quality = quality

        self._setup()

    def _setup(self):
        self.setText(self._get_text())

    def _get_text(self):
        return ''

    @property
    def quality(self):
        return self._quality


class QBitrateResQualityButton(_QQualityButton):

    def _get_text(self):
        return '{} kbps ({}p)'.format(self.quality.bitrate // 1000,
                                      self.quality.yres)


class QSymbolicQualityButton(_QQualityButton):

    def _get_text(self):
        texts = {
            SymbolicQuality.LOWEST: 'Lowest quality',
            SymbolicQuality.AVERAGE: 'Average quality',
            SymbolicQuality.HIGHEST: 'Highest quality',
        }
        return texts[self.quality]


class QChooseBitrateDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'choose_bitrate_dialog'

    bitrate_chosen = QtCore.pyqtSignal(object, list)

    def __init__(self, episodes, qualities, btn_class):
        super().__init__()

        self._episodes = episodes
        self._qualities = qualities
        self._btn_class = btn_class

        self._setup_ui()

    def _setup_ui(self):
        self._load_ui(QChooseBitrateDialog._UI_NAME)
        self._populate_qualities_buttons()
        self.adjustSize()
        self.setFixedHeight(self.height())
        self.setFixedWidth(self.width())

    def _populate_qualities_buttons(self):
        for quality in self._qualities:
            btn = self._btn_class(quality)
            btn.clicked.connect(self._on_quality_btn_clicked)
            btn.adjustSize()
            self.buttons_vbox.addWidget(btn)

    def _on_quality_btn_clicked(self):
        btn = self.sender()
        quality = btn.quality
        self.close()
        self.bitrate_chosen.emit(quality, self._episodes)

    def show_move(self, pos):
        super().show_move(pos)
