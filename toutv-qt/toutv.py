# stdlib imports
import signal
import sys

# PyQt4 imports
from PyQt4 import uic
from PyQt4 import Qt

from shows_treemodel import ShowsTreeModel, FakeDataSource

TOUTV_UI_FILE = "toutv.ui"

class TouTvQt(Qt.QApplication):
	def __init__(self, args):
		super(TouTvQt, self).__init__(args)

	def setup_ui(self, mainwindow):
		"""Setup signal/slot connections"""
		self.mainwindow = mainwindow

		self.mainwindow.action_quit.triggered.connect(self.closeAllWindows)

		data = FakeDataSource("fakedata.xml")
		model = ShowsTreeModel(data)
		self.mainwindow.shows_treeview.setModel(model)

if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app = TouTvQt(sys.argv)
	mainwindow = uic.loadUi(TOUTV_UI_FILE)
	app.setup_ui(mainwindow)
	mainwindow.show()
	app.exec_()
