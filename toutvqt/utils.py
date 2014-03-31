import os.path
from pkg_resources import resource_filename
from PyQt4 import Qt
from PyQt4 import uic


class QCommonDialog(Qt.QDialog):
    def __init__(self):
        super(QCommonDialog, self).__init__()

    def show_move(self, pos):
        self.move(pos)
        self.exec()


class QtUiLoad:
    _UI_DIR = os.path.join('dat', 'ui')

    def _load_ui(self, ui_name):
        ui_rel_path = os.path.join(QtUiLoad._UI_DIR, '{}.ui'.format(ui_name))
        ui_path = resource_filename(__name__, ui_rel_path)
        uic.loadUi(ui_path, baseinstance=self)



def load_qt_ui(ui_name, baseinstance):
    ui_rel_path = os.path.join(QtUiLoad._UI_DIR, '{}.ui'.format(ui_name))
    ui_path = resource_filename(__name__, ui_rel_path)
    uic.loadUi(ui_path, baseinstance=baseinstance)
