from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.emissions_treeview import QEmissionsTreeView


class QTouTvMainWindow(Qt.QMainWindow):
    UI_PATH = resource_filename(__name__, 'dat/main_window.ui')

    def __init__(self, app):
        super(QTouTvMainWindow, self).__init__()

        self._app = app

        self._setup_ui()
        self._setup_signals()

    def _add_treeview(self):
        self.emissions_treeview = QEmissionsTreeView()
        layout = self.emissions_tab.layout()
        layout.insertWidget(0, self.emissions_treeview)

    def _setup_signals(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_ui(self):
        uic.loadUi(QTouTvMainWindow.UI_PATH, baseinstance=self)
        self._add_treeview()
