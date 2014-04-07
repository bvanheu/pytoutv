from PyQt4 import Qt
from PyQt4 import QtCore


class QDlItemDelegate(Qt.QItemDelegate):

    def __init__(self, model):
        super().__init__(model)
        self._model = model

    @staticmethod
    def _get_progress_bar(option, percent):
        p = Qt.QStyleOptionProgressBarV2()

        p.state = Qt.QStyle.State_Enabled
        p.direction = Qt.QApplication.layoutDirection()
        p.rect = option.rect
        p.fontMetrics = Qt.QApplication.fontMetrics()
        p.minimum = 0
        p.maximum = 100
        p.textAlignment = QtCore.Qt.AlignCenter
        p.textVisible = True
        p.progress = percent
        p.text = '{}%'.format(percent)

        return p

    def paint(self, painter, option, index):
        # Mostly taken from:
        # http://qt-project.org/doc/qt-4.8/network-torrent-mainwindow-cpp.html

        if index.column() != self._model.get_progress_col():
            super().paint(painter, option, index)
            return

        dl_item = self._model.get_download_item_at_row(index.row())
        percent = dl_item.get_progress_percent()

        progress_bar = QDlItemDelegate._get_progress_bar(option, percent)

        style = Qt.QApplication.style()
        style.drawControl(Qt.QStyle.CE_ProgressBar, progress_bar, painter)
