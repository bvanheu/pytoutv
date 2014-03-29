from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore


class QDownloadsTableView(Qt.QTableView):
    def __init__(self, model):
        super(QDownloadsTableView, self).__init__()

        self._setup(model)

    def _setup(self, model):
        self.setModel(model)

        # Hide vertical header
        self.verticalHeader().hide()

        # Stretch horizontally
        stretch_mode = Qt.QHeaderView.Stretch
        self.horizontalHeader().setResizeMode(stretch_mode)

        # Select rows, not cells
        sel_rows_behavior = Qt.QAbstractItemView.SelectRows
        self.setSelectionBehavior(sel_rows_behavior)

        # Do not highlight header when selecting a row
        self.horizontalHeader().setHighlightSections(False)

    def set_default_columns_widths(self):
        pass
