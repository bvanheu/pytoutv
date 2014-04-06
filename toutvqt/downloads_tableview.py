from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore
from toutvqt.downloads_itemdelegate import QDlItemDelegate
from toutvqt import utils


class QDownloadsTableView(Qt.QTreeView):
    cancel_download = QtCore.pyqtSignal(int)

    def __init__(self, model):
        super().__init__()

        self.setRootIsDecorated(False)
        self.setItemDelegate(QDlItemDelegate(model))
        self._setup(model)

    def _build_context_menu(self):
        self._context_menu = Qt.QMenu(parent=self)

        # Actions
        self._open_action = self._context_menu.addAction('&Open')
        self._open_dir_action = self._context_menu.addAction('&Open directory in file explorer')
        self._cancel_action = self._context_menu.addAction('&Cancel')

        # Icons
        self._open_action.setIcon(utils.get_qicon('open_action'))
        self._open_dir_action.setIcon(utils.get_qicon('open_dir_action'))
        self._cancel_action.setIcon(utils.get_qicon('cancel_action'))

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
            output_dir = dl_item.get_work().get_output_dir()
            filename = dl_item.get_filename()
            url = Qt.QUrl("file://{}/{}".format(output_dir, filename))
            Qt.QDesktopServices.openUrl(url)

        elif action is self._open_dir_action:
            output_dir = dl_item.get_work().get_output_dir()
            url = Qt.QUrl("file://{}".format(output_dir))
            Qt.QDesktopServices.openUrl(url)

        elif action is self._cancel_action:
            self.cancel_download.emit(index.row())

    def set_default_columns_widths(self):
        pass
