# stdlib imports
import sys

# PyQt4 imports
from PyQt4 import uic
from PyQt4 import Qt

TOUTV_UI_FILE = "toutv.ui"

class TouTvQt(Qt.QApplication):
	def __init__(self, args):
		super(TouTvQt, self).__init__(args)




if __name__ == '__main__':
	app = TouTvQt(sys.argv)
	ui = uic.loadUi(TOUTV_UI_FILE)
	ui.show()
	app.exec_()
