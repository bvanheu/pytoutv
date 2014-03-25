from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.emissions_treemodel import EmissionsTreeModel
from toutvqt.emissions_treemodel import FakeDataSource


class QTouTvMainWindow(Qt.QMainWindow):
    UI_PATH = resource_filename(__name__, 'dat/main_window.ui')

    def __init__(self, app):
        super(QTouTvMainWindow, self).__init__()

        self._app = app

        self._setup_ui()
        self._setup_signals()
        self._setup_treeview()

    def _setup_treeview(self):
        xml_path = resource_filename(__name__, 'dat/fakedata.xml')
        data = FakeDataSource(xml_path)
        model = EmissionsTreeModel(data)

        # TODO: move treeview to own class
        self.emissions_treeview.setModel(model)
        self.emissions_treeview.expanded.connect(model.itemExpanded)

    def _setup_signals(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_ui(self):
        uic.loadUi(QTouTvMainWindow.UI_PATH, baseinstance=self)
