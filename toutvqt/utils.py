import os.path
from pkg_resources import resource_filename
from PyQt4 import uic


_UI_DIR = os.path.join('dat', 'ui')


def load_qt_ui(ui_name, baseinstance):
    ui_rel_path = os.path.join(_UI_DIR, '{}.ui'.format(ui_name))
    ui_path = resource_filename(__name__, ui_rel_path)
    uic.loadUi(ui_path, baseinstance=baseinstance)
