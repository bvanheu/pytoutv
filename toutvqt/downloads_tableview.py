from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore
from toutvqt.downloads_itemdelegate import QDlItemDelegate


class QDownloadsTableView(Qt.QTreeView):
    def __init__(self, model):
        super().__init__()

        self.setRootIsDecorated(False)
        self.setItemDelegate(QDlItemDelegate(model))
        self._setup(model)

    def _build_context_menu(self):
        self._context_menu = Qt.QMenu(parent=self)
        self._open_action = self._context_menu.addAction('&Open')
        self._open_dir_action = self._context_menu.addAction('&Open directory in file explorer')
        self._cancel_action = self._context_menu.addAction('&Cancel')

    def _setup_context_menu(self):
        self._build_context_menu()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _setup(self, model):
        self.setModel(model)
        self._setup_context_menu()

    def _on_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return

        dl_item = self.model().get_download_item_at_row(index.row())
        print(dl_item.get_filename())

        action = self._context_menu.exec(Qt.QCursor.pos())

        if action is self._open_action:
            print("open!", index.isValid())
            pass
        elif action is self._open_dir_action:
            url = QUrl("file:// " + dl_item.get_output_dir())
            Qt.QDesktopServices.openUrl(url);

        elif action is self._cancel_action:
            print("cancel!", index.isValid())
            pass

    def set_default_columns_widths(self):
        pass
