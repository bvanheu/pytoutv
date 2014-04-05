import os.path
from pkg_resources import resource_filename
from PyQt4 import Qt
from PyQt4 import uic
from toutvqt import config


class QCommonDialog(Qt.QDialog):
    def __init__(self):
        super().__init__()

    def show_move(self, pos):
        self.move(pos)
        self.exec()


class QtUiLoad:
    def _load_ui(self, ui_name):
        ui_rel_path = os.path.join(config.UI_DIR, '{}.ui'.format(ui_name))
        ui_path = resource_filename(__name__, ui_rel_path)
        uic.loadUi(ui_path, baseinstance=self)


def get_qicon(name):
    filename = '{}.png'.format(name)
    rel_path = os.path.join(config.ICONS_DIR, filename)
    path = resource_filename(__name__, rel_path)

    return Qt.QIcon(path)
