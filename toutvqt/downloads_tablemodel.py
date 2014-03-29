from PyQt4 import Qt
from PyQt4 import QtCore


class QDownloadsTableModel(Qt.QAbstractTableModel):
    _HEADER = [
        'Emission',
        'Season',
        'Episode',
        'Filename',
        'Sections',
        'Bytes',
        'Progress',
        '%',
    ]

    def __init__(self, parent=None):
        super(QDownloadsTableModel, self).__init__(parent)

    def rowCount(self, parent):
        return 5

    def columnCount(self, parent):
        return len(QDownloadsTableModel._HEADER)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return '{}, {}'.format(index.row(), index.column())

    def headerData(self, col, ori, role):
        if ori == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return QDownloadsTableModel._HEADER[col]

        return None

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        pass

        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(SIGNAL("layoutChanged()"))
