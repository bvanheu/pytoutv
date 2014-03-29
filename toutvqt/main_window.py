from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from toutvqt.emissions_treeview import QEmissionsTreeView
from toutvqt.emissions_treemodel import EmissionsTreeModel
from toutvqt.about_dialog import QTouTvAboutDialog
from toutvqt.preferences_dialog import QTouTvPreferencesDialog
from toutvqt.infos_frame import QInfosFrame

from toutv import client


class QTouTvMainWindow(Qt.QMainWindow):
    UI_PATH = resource_filename(__name__, 'dat/ui/main_window.ui')

    def __init__(self, app, client):
        super(QTouTvMainWindow, self).__init__()

        self._app = app
        self._client = client

        self._setup_ui()

    def _add_treeview(self):
        treeview_model = EmissionsTreeModel(self._client)
        self.emissions_treeview = QEmissionsTreeView(treeview_model)
        self.emissions_tab.layout().addWidget(self.emissions_treeview)

    def _add_infos(self):
        self.infos_frame = QInfosFrame()
        self.emissions_tab.layout().addWidget(self.infos_frame)
        treeview = self.emissions_treeview
        treeview.emission_selected.connect(self.infos_frame.show_emission)
        treeview.season_selected.connect(self.infos_frame.show_season)
        treeview.episode_selected.connect(self.infos_frame.show_episode)
        treeview.none_selected.connect(self.infos_frame.show_infos_none)

    def _setup_file_menu(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)

    def _setup_edit_menu(self):
        self.preferences_dialog = QTouTvPreferencesDialog()
        self.preferences_action.triggered.connect(self.show_preferences_dialog)

    def _setup_help_menu(self):
        self.about_dialog = QTouTvAboutDialog()
        self.about_action.triggered.connect(self.show_about_dialog)

    def _setup_menus(self):
        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_help_menu()

    @staticmethod
    def _get_icon(name):
        path = resource_filename(__name__, 'dat/icons/{}.png'.format(name))

        return Qt.QIcon(path)

    def _setup_action_icon(self, action_name):
        action = getattr(self, action_name)
        icon = QTouTvMainWindow._get_icon(action_name)
        action.setIcon(icon)

    def _setup_icons(self):
        self.setWindowIcon(QTouTvMainWindow._get_icon('toutv'))
        self._setup_action_icon('refresh_emissions_action')
        self._setup_action_icon('preferences_action')
        self._setup_action_icon('about_action')

    def _setup_ui(self):
        uic.loadUi(QTouTvMainWindow.UI_PATH, baseinstance=self)
        self._setup_icons()
        self._add_treeview()
        self._add_infos()
        self._setup_menus()

    def _setup_ui_post_show(self):
        self.emissions_treeview.set_default_columns_widths()

    def start(self):
        # Let's start downloading the root elements
        self.emissions_treeview.model().init_fetch()
        self.show()
        self._setup_ui_post_show()

    def show_about_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 40)
        pos.setY(pos.y() + 40)
        self.about_dialog.show_move(pos)

    def show_preferences_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 60)
        pos.setY(pos.y() + 60)
        self.preferences_dialog.show_move(pos)
