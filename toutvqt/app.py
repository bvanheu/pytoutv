import signal
import sys
from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.emissions_treemodel import EmissionsTreeModel, FakeDataSource


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
        model = EmissionsTreeModel(data)
        self.mainwindow.emissions_treeview.setModel(model)
        self.mainwindow.emissions_treeview.expanded.connect(model.itemExpanded)


def run():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = TouTvQt(sys.argv)
    mainwindow = uic.loadUi(TOUTV_UI_FILE)
    app.setup_ui(mainwindow)
    mainwindow.show()
    app.exec_()
