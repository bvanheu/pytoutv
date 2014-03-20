# stdlib imports
import sys

# PyQt4 imports
from PyQt4 import uic
from PyQt4 import Qt

TOUTV_UI_FILE = "toutv.ui"

class TouTvQt(Qt.QApplication):
	def __init__(self, args):
		super(TouTvQt, self).__init__(args)

	def setup_ui(self, mainwindow):
		"""Setup signal/slot connections"""
		self.mainwindow = mainwindow

		self.mainwindow.action_quit.triggered.connect(self.closeAllWindows)

if __name__ == '__main__':
	app = TouTvQt(sys.argv)
	mainwindow = uic.loadUi(TOUTV_UI_FILE)
	app.setup_ui(mainwindow)
	mainwindow.show()
	app.exec_()
