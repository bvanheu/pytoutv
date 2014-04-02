from PyQt4 import Qt
from PyQt4 import QtCore


class QDownloadsItemDeletate(Qt.QItemDelegate):
    def __init__(self, model):
        super().__init__(model)
        self._model = model

    def paint(self, painter, option, index):
        # Mostly taken from:
        # http://qt-project.org/doc/qt-4.8/network-torrent-mainwindow-cpp.html

        if index.column() != self._model.get_progress_col():
            super().paint(painter, option, index)
            return

        work, progress = self._model.get_download_at_row(index.row())
        segments_done = progress.get_done_segments_count()
        segments_total = progress.get_total_segments_count()

        p = Qt.QStyleOptionProgressBarV2()

        p.state = Qt.QStyle.State_Enabled
        p.direction = Qt.QApplication.layoutDirection()
        p.rect = option.rect
        p.fontMetrics = Qt.QApplication.fontMetrics()
        p.minimum = 0
        p.maximum = 100
        p.textAlignment = QtCore.Qt.AlignCenter
        p.textVisible = True

        percentage = 100 * segments_done // segments_total

        p.progress = percentage
        p.text = '{} %'.format(percentage)

        style = Qt.QApplication.style()
        style.drawControl(Qt.QStyle.CE_ProgressBar, p, painter)
