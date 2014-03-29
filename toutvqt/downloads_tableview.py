from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore


class QDownloadsTableView(Qt.QTableView):
    def __init__(self):
        super(QDownloadsTableView, self).__init__()

        self._setup(None)

    def _setup(self, model):
        pass

    def set_default_columns_widths(self):
        pass
