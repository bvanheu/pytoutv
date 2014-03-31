import os.path
from pkg_resources import resource_filename
from PyQt4 import Qt
from PyQt4 import QtCore
from PyQt4 import QtGui
from toutvqt.download_manager import QDownloadManager
from toutvqt.downloads_tablemodel import QDownloadsTableModel
from toutvqt.downloads_tableview import QDownloadsTableView
from toutvqt.emissions_treeview import QEmissionsTreeView
from toutvqt.emissions_treemodel import EmissionsTreeModel
from toutvqt.about_dialog import QTouTvAboutDialog
from toutvqt.preferences_dialog import QTouTvPreferencesDialog
from toutvqt.choose_bitrate_dialog import QChooseBitrateDialog
from toutvqt.infos_frame import QInfosFrame
from toutvqt import utils
from toutvqt import config
from toutv import client


class QTouTvMainWindow(Qt.QMainWindow, utils.QtUiLoad):
    _UI_NAME = 'main_window'

    def __init__(self, app, client):
        super(QTouTvMainWindow, self).__init__()

        self._app = app
        self._client = client

        self._setup_ui()

    def _add_treeview(self):
        model = EmissionsTreeModel(self._client)
        self._treeview_model = model
        self.emissions_treeview = QEmissionsTreeView(model)
        self.emissions_tab.layout().addWidget(self.emissions_treeview)

    def _add_tableview(self):
        self._download_manager = QDownloadManager()
        model = QDownloadsTableModel(self._download_manager)
        self._downloads_tableview_model = model
        self.downloads_tableview = QDownloadsTableView(model)
        self.downloads_tab.layout().addWidget(self.downloads_tableview)

    def _add_infos(self):
        self.infos_frame = QInfosFrame()
        self.infos_frame.select_download.connect(self._on_select_download)
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
        _show_prefs_cb = self._show_preferences_dialog
        self.preferences_action.triggered.connect(_show_prefs_cb)

    def _setup_help_menu(self):
        self.about_dialog = QTouTvAboutDialog()
        self.about_action.triggered.connect(self._show_about_dialog)

    def _setup_menus(self):
        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_help_menu()

    def _setup_action_icon(self, action_name):
        action = getattr(self, action_name)
        icon = utils.get_qicon(action_name)
        action.setIcon(icon)

    def _setup_icons(self):
        self.setWindowIcon(utils.get_qicon('toutv'))
        self._setup_action_icon('refresh_emissions_action')
        self._setup_action_icon('preferences_action')
        self._setup_action_icon('about_action')

    def _setup_ui(self):
        self._load_ui(QTouTvMainWindow._UI_NAME)
        self._setup_icons()
        self._add_treeview()
        self._add_infos()
        self._add_tableview()
        self._setup_menus()

    def closeEvent(self, close_event):
        self.infos_frame.exit()
        self._downloads_tableview_model.exit()
        self._treeview_model.exit()

    def _setup_ui_post_show(self):
        self.emissions_treeview.set_default_columns_widths()

    def start(self):
        self.emissions_treeview.model().init_fetch()
        self.show()
        self._setup_ui_post_show()

    def _show_about_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 40)
        pos.setY(pos.y() + 40)
        self.about_dialog.show_move(pos)

    def _show_preferences_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 60)
        pos.setY(pos.y() + 60)
        self.preferences_dialog.show_move(pos)

    def _on_select_download(self, episode):
        pos = QtGui.QCursor().pos()
        cursor = self.cursor()
        self.setCursor(QtCore.Qt.WaitCursor)
        bitrates = episode.get_available_bitrates()
        self.setCursor(cursor)
        if len(bitrates) > 1:
            dialog = QChooseBitrateDialog(episode, bitrates)
            dialog.bitrate_chosen.connect(self._on_bitrate_chosen)
            pos.setX(pos.x() - dialog.width())
            pos.setY(pos.y() - dialog.height())
            dialog.show_move(pos)
        else:
            print('single bitrate: {}'.format(bitrate[0]))
            self._on_bitrate_chosen(bitrate[0])

    def _on_bitrate_chosen(self, bitrate, episode):
        print('chose {} bps'.format(bitrate))
        self._download_manager.download(episode, bitrate)
