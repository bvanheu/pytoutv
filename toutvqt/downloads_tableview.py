from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore
from toutvqt.downloads_itemdelegate import QDownloadsItemDeletate


class QDownloadsTableView(Qt.QTreeView):

    def __init__(self, model):
        super().__init__()

        self.setRootIsDecorated(False)
        self.setItemDelegate(QDownloadsItemDeletate(model))
        self._setup(model)

    def _setup(self, model):
        self.setModel(model)

    def set_default_columns_widths(self):
        pass
