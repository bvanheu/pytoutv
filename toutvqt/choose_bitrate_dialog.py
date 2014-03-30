from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4 import QtCore


class QChooseBitrateDialog(Qt.QDialog):
    _UI_PATH = resource_filename(__name__, 'dat/ui/choose_bitrate_dialog.ui')
    bitrate_chosen = QtCore.pyqtSignal(int)

    def __init__(self, bitrates):
        super(QChooseBitrateDialog, self).__init__()

        self._bitrates = bitrates
        self._setup_ui()

    def _setup_ui(self):
        uic.loadUi(QChooseBitrateDialog._UI_PATH, baseinstance=self)

    def _populateBitrateButtons(self):
        for bitrate in self._bitrates:
            btn = QBitrateButton(bitrate)
            text = '{} kbps'.format(bitrate // 1000)
            btn.setText(text)
            btn.clicked.connect(self._on_bitrate_btn_clicked)
            self.buttons_vbox.addWidget(btn)

    def _on_bitrate_btn_clicked(self):
        btn = self.sender()
        self.bitrate_chosen.emit(btn.get_bitrate())
        self.close()

    def show_move(self, pos):
        self.move(pos)
        self._populateBitrateButtons()
        self.exec()


class QBitrateButton(Qt.QPushButton):
    def __init__(self, bitrate):
        super(QBitrateButton, self).__init__()

        self._bitrate = bitrate

    def get_bitrate(self):
        return self._bitrate
