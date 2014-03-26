from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.emissions_treeview import QEmissionsTreeView
from toutvqt.about_dialog import QTouTvAboutDialog
from toutvqt.infos_frame import QInfosFrame


class QTouTvMainWindow(Qt.QMainWindow):
    UI_PATH = resource_filename(__name__, 'dat/main_window.ui')

    def __init__(self, app):
        super(QTouTvMainWindow, self).__init__()

        self._app = app

        self._setup_ui()

    def _add_treeview(self):
        self.emissions_treeview = QEmissionsTreeView()
        self.emissions_tab.layout().addWidget(self.emissions_treeview)

    def _add_infos(self):
        self.infos_frame = QInfosFrame()
        self.emissions_tab.layout().addWidget(self.infos_frame)

    def _setup_file_menu(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_edit_menu(self):
        pass

    def _setup_help_menu(self):
        self.about_dialog = QTouTvAboutDialog()
        self.about_action.triggered.connect(self.show_about_dialog)

    def _setup_menus(self):
        self._setup_file_menu()
        self._setup_help_menu()

    def _setup_infos(self):
        self.infos_frame = QInfosFrame()

    def _setup_ui(self):
        uic.loadUi(QTouTvMainWindow.UI_PATH, baseinstance=self)
        self._add_treeview()
        self._add_infos()
        self._setup_menus()
        self._setup_infos()

    def show_about_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 40)
        pos.setY(pos.y() + 40)
        self.about_dialog.show_move(pos)
