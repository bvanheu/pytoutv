from PyQt4 import Qt, QtCore
from toutvqt.downloads_itemdelegate import QDlItemDelegate
from toutvqt.downloads_tablemodel import DownloadItemState
from toutvqt import utils


class QDownloadsTableView(Qt.QTreeView):
    def __init__(self, model):
        super().__init__()

        self.setRootIsDecorated(False)
        self.setItemDelegate(QDlItemDelegate(model))
        self._setup(model)

    def _build_context_menu(self):
        self._context_menu = Qt.QMenu(parent=self)

        # Actions
        self._remove_item_action = self._context_menu.addAction('Remove item')
        self._cancel_action = self._context_menu.addAction('Cancel')
        self._open_action = self._context_menu.addAction('Open')
        self._open_dir_action = self._context_menu.addAction('Open directory')

        # Icons
        self._remove_item_action.setIcon(utils.get_qicon('remove_item_action'))
        self._open_action.setIcon(utils.get_qicon('open_action'))
        self._open_dir_action.setIcon(utils.get_qicon('open_dir_action'))
        self._cancel_action.setIcon(utils.get_qicon('cancel_action'))

        self._visible_context_menu_actions = {
            DownloadItemState.QUEUED: [
                self._cancel_action,
                self._open_dir_action,
            ],
            DownloadItemState.RUNNING: [
                self._cancel_action,
                self._open_action,
                self._open_dir_action,
            ],
            DownloadItemState.PAUSED: [
                self._cancel_action,
                self._open_action,
                self._open_dir_action,
            ],
            DownloadItemState.CANCELLED: [
                self._remove_item_action,
                self._open_dir_action,
            ],
            DownloadItemState.ERROR: [
                self._remove_item_action,
                self._open_dir_action,
            ],
            DownloadItemState.DONE: [
                self._remove_item_action,
                self._open_action,
                self._open_dir_action,
            ],
        }

    def _setup_context_menu(self):
        self._build_context_menu()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _setup(self, model):
        self.setModel(model)
        self._setup_context_menu()

    def _arrange_context_menu(self, dl_item_state):
        self._remove_item_action.setVisible(False)
        self._cancel_action.setVisible(False)
        self._open_action.setVisible(False)
        self._open_dir_action.setVisible(False)

        for action in self._visible_context_menu_actions[dl_item_state]:
            action.setVisible(True)

    def _on_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return

        dl_item = self.model().get_download_item_at_row(index.row())

        self._arrange_context_menu(dl_item.get_state())
        action = self._context_menu.exec(Qt.QCursor.pos())

        if action is self._open_action:
            output_dir = dl_item.get_work().get_output_dir()
            filename = dl_item.get_filename()
            url = Qt.QUrl('file://{}/{}'.format(output_dir, filename))
            Qt.QDesktopServices.openUrl(url)
        elif action is self._open_dir_action:
            output_dir = dl_item.get_work().get_output_dir()
            url = Qt.QUrl('file://{}'.format(output_dir))
            Qt.QDesktopServices.openUrl(url)
        elif action is self._cancel_action:
            self.model().cancel_download_at_row(index.row())
        elif action is self._remove_item_action:
            self.model().remove_item_at_row(index.row())

    def set_default_columns_widths(self):
        pass
