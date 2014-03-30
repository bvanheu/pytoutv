from PyQt4 import Qt
from PyQt4 import QtCore


class QDownloadsItemDeletate(Qt.QItemDelegate):
    PROGRESS_COL_NUM = 6

    def __init__(self, parent=None):
        super(QDownloadsItemDeletate, self).__init__(parent)

    def paint(self, painter, option, index):
        # Mostly taken from:
        # http://qt-project.org/doc/qt-4.8/network-torrent-mainwindow-cpp.html
        if index.column() != self.PROGRESS_COL_NUM:
            super(QDownloadsItemDeletate, self).paint(painter, option, index)
            return

        p = Qt.QStyleOptionProgressBarV2()

        p.state = Qt.QStyle.State_Enabled
        p.direction = Qt.QApplication.layoutDirection()
        p.rect = option.rect
        p.fontMetrics = Qt.QApplication.fontMetrics()
        p.minimum = 0
        p.maximum = 100
        p.textAlignment = QtCore.Qt.AlignCenter
        p.textVisible = True

        progress = 43

        p.progress = progress
        p.text = "43 %"

        Qt.QApplication.style().drawControl(
            Qt.QStyle.CE_ProgressBar, p, painter)
