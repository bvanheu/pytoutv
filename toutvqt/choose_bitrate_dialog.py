from PyQt4 import Qt
from PyQt4 import QtCore
from toutvqt import utils


_VIDEO_RESOLUTIONS = [
    270,
    288,
    360,
    480
]


class _QQualityButton(Qt.QPushButton):
    def __init__(self, bitrate, res_index):
        super().__init__()

        self._bitrate = bitrate
        self._res = _VIDEO_RESOLUTIONS[res_index]
        self._res_index = res_index

        self._setup()

    def _setup(self):
        self.setText(self._get_text())

    def _get_text(self):
        return ''

    def get_bitrate(self):
        return self._bitrate

    def get_res_index(self):
        return self._res_index


class QBitrateResQualityButton(_QQualityButton):
    def _get_text(self):
        return '{} kbps ({}p)'.format(self._bitrate // 1000, self._res)


class QResQualityButton(_QQualityButton):
    def _get_text(self):
        return '{}p'.format(self._res)


class QChooseBitrateDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'choose_bitrate_dialog'
    bitrate_chosen = QtCore.pyqtSignal(int, list)

    def __init__(self, episodes, bitrates, btn_class):
        super().__init__()

        self._episodes = episodes
        self._bitrates = bitrates
        self._btn_class = btn_class

        self._setup_ui()

    def _setup_ui(self):
        self._load_ui(QChooseBitrateDialog._UI_NAME)
        self._populate_bitrate_buttons()
        self.adjustSize()
        self.setFixedHeight(self.height())
        self.setFixedWidth(self.width())

    def _populate_bitrate_buttons(self):
        for res_index, bitrate in enumerate(self._bitrates):
            btn = self._btn_class(bitrate, res_index)
            btn.clicked.connect(self._on_bitrate_btn_clicked)
            btn.adjustSize()
            self.buttons_vbox.addWidget(btn)

    def _on_bitrate_btn_clicked(self):
        btn = self.sender()
        res_index = btn.get_res_index()
        self.close()
        self.bitrate_chosen.emit(res_index, self._episodes)

    def show_move(self, pos):
        super().show_move(pos)
