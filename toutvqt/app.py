# stdlib imports
import signal
import sys

# egg
from pkg_resources import resource_filename

# PyQt4 imports
from PyQt4 import uic
from PyQt4 import Qt

from toutvqt.shows_treemodel import ShowsTreeModel, FakeDataSource

TOUTV_UI_FILE = resource_filename(__name__, 'dat/toutv.ui')

class TouTvQt(Qt.QApplication):
    def __init__(self, args):
        super(TouTvQt, self).__init__(args)

    def setup_ui(self, mainwindow):
        """Setup signal/slot connections"""
        self.mainwindow = mainwindow

        self.mainwindow.action_quit.triggered.connect(self.closeAllWindows)

        xml_path = resource_filename(__name__, 'dat/fakedata.xml')
        data = FakeDataSource(xml_path)
        model = ShowsTreeModel(data)
        self.mainwindow.shows_treeview.setModel(model)
        self.mainwindow.shows_treeview.expanded.connect(model.itemExpanded)


def run():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = TouTvQt(sys.argv)
    mainwindow = uic.loadUi(TOUTV_UI_FILE)
    app.setup_ui(mainwindow)
    mainwindow.show()
    app.exec_()
