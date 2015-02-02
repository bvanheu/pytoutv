import os.path
import logging
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
from toutvqt.choose_bitrate_dialog import QChooseBitrateDialog, SymbolicQuality,\
    QSymbolicQualityButton
from toutvqt.choose_bitrate_dialog import QBitrateResQualityButton
from toutvqt.infos_frame import QInfosFrame
from toutvqt import utils
from toutv import exceptions


class QTouTvMainWindow(Qt.QMainWindow, utils.QtUiLoad):
    _UI_NAME = 'main_window'
    settings_accepted = QtCore.pyqtSignal(dict)

    def __init__(self, app, client):
        super().__init__()

        self._app = app
        self._client = client

        self._setup_ui()

    def _add_treeview(self):
        model = EmissionsTreeModel(self._client)
        model.fetching_start.connect(self._on_treeview_fetch_start)
        model.fetching_done.connect(self._on_treeview_fetch_done)
        self._treeview_model = model

        treeview = QEmissionsTreeView(model)
        self.emissions_treeview = treeview
        self.emissions_tab.layout().addWidget(treeview)

    def _add_tableview(self):
        settings = self._app.get_settings()
        nb_threads = settings.get_download_slots()
        self._download_manager = QDownloadManager(nb_threads=nb_threads)

        model = QDownloadsTableModel(self._download_manager)
        model.download_finished.connect(self._on_download_finished)
        model.download_cancelled.connect(self._on_download_finished)
        self._downloads_tableview_model = model

        tableview = QDownloadsTableView(model)
        self.downloads_tableview = tableview
        self.downloads_tab.layout().addWidget(tableview)

    def _add_infos(self):
        self.infos_frame = QInfosFrame(self._client)
        self.infos_frame.select_download.connect(self._on_select_download)
        self.emissions_tab.layout().addWidget(self.infos_frame)
        treeview = self.emissions_treeview
        treeview.emission_selected.connect(self.infos_frame.show_emission)
        treeview.season_selected.connect(self.infos_frame.show_season)
        treeview.episode_selected.connect(self.infos_frame.show_episode)
        treeview.none_selected.connect(self.infos_frame.show_infos_none)

    def _setup_file_menu(self):
        self.quit_action.triggered.connect(self._app.closeAllWindows)
        self.refresh_emissions_action.triggered.connect(
            self._treeview_model.reset)

    def _setup_edit_menu(self):
        self.preferences_action.triggered.connect(
            self._show_preferences_dialog)

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
        self._setup_action_icon('quit_action')
        self._setup_action_icon('refresh_emissions_action')
        self._setup_action_icon('preferences_action')
        self._setup_action_icon('about_action')

    def _setup_statusbar(self):
        # Hide status bar until implemented
        self.statusbar.hide()

    def _setup_errormsg(self):
        self._error_msg_dialog = Qt.QErrorMessage(self)

    def _setup_ui(self):
        self._load_ui(QTouTvMainWindow._UI_NAME)
        self._setup_icons()
        self._add_treeview()
        self._add_infos()
        self._add_tableview()
        self._setup_menus()
        self._setup_statusbar()
        self._setup_errormsg()

    def closeEvent(self, close_event):
        logging.debug('Closing main window')
        self._set_wait_cursor()
        self.infos_frame.exit()
        self._downloads_tableview_model.exit()
        self._treeview_model.exit()

    def _setup_ui_post_show(self):
        self.emissions_treeview.set_default_columns_widths()

    def start(self):
        logging.debug('Starting main window')
        self.emissions_treeview.model().init_fetch()
        self.show()
        self._setup_ui_post_show()

    def _show_about_dialog(self):
        pos = self.pos()
        pos.setX(pos.x() + 40)
        pos.setY(pos.y() + 40)
        self.about_dialog.show_move(pos)

    def _show_preferences_dialog(self):
        settings = QTouTvPreferencesDialog(self._app.get_settings())
        settings.settings_accepted.connect(self.settings_accepted)
        pos = self.pos()
        pos.setX(pos.x() + 60)
        pos.setY(pos.y() + 60)
        settings.show_move(pos)

    def _set_wait_cursor(self):
        self.setCursor(QtCore.Qt.WaitCursor)

    def _set_normal_cursor(self):
        self.setCursor(QtCore.Qt.ArrowCursor)

    def _on_download_finished(self, work):
        settings = self._app.get_settings()

        if settings.get_remove_finished():
            eid = work.get_episode().get_id()
            self._downloads_tableview_model.remove_episode_id_item(eid)

    def _on_treeview_fetch_start(self):
        self.refresh_emissions_action.setEnabled(False)

    def _on_treeview_fetch_done(self):
        self.refresh_emissions_action.setEnabled(True)

    def _show_choose_bitrate_dialog(self, episodes, qualities, btn_class):
        pos = QtGui.QCursor().pos()
        dialog = QChooseBitrateDialog(
            episodes, qualities, btn_class)
        dialog.bitrate_chosen.connect(self._on_quality_chosen)
        pos.setX(pos.x() - dialog.width())
        pos.setY(pos.y() - dialog.height())
        dialog.show_move(pos)

    def _on_select_download_single(self, episodes):
        logging.debug('Single episode selected for download')

        assert len(episodes) == 1

        ''' Get available qualities '''
        try:
            self._set_wait_cursor()
            qualities = episodes[0].get_available_qualities()
            btn_class = QBitrateResQualityButton

            settings = self._app.get_settings()
            if settings.get_always_max_quality():
                ''' Assume the qualities are ordered from low to high '''
                self._on_quality_chosen(qualities[-1], episodes)
            else:
                self._show_choose_bitrate_dialog(episodes, qualities,
                                                 btn_class)

        except exceptions.UnexpectedHttpStatusCodeError:
            self._error_msg_dialog.showMessage(
                'Could not download episode playlist. It might not be '
                'available yet.')
            return
        finally:
            self._set_normal_cursor()

    def _on_select_download_multi(self, episodes):
        logging.debug('Multiple episodes selected for download')
        qualities = list(SymbolicQuality)
        btn_class = QSymbolicQualityButton

        settings = self._app.get_settings()
        if settings.get_always_max_quality():
            self._on_quality_chosen(SymbolicQuality.HIGHEST, episodes)
        else:
            self._show_choose_bitrate_dialog(episodes, qualities, btn_class)

    def _on_select_download(self, episodes):
        ''' User clicked on the download button '''
        if len(episodes) == 1:
            self._on_select_download_single(episodes)
        elif len(episodes) > 1:
            self._on_select_download_multi(episodes)

    def _start_download(self, episode, quality, output_dir):
        # Fixme: download_item_exists should take the qu ality as well
        if self._downloads_tableview_model.download_item_exists(
                episode.get_id(), quality):
            tmpl = 'Download of episode "{}" @ {} bps already exists'
            logging.info(tmpl.format(episode.get_title(), quality.bitrate))
            return

        self._download_manager.download(episode, quality, output_dir,
                                        proxies=self._app.get_proxies())

    def start_download_episode_single(self, quality, episode, output_dir):
        self._set_wait_cursor()

        tmpl = 'Queueing download of episode "{}" @ {} bps'
        logging.debug(tmpl.format(episode.get_title(), quality.bitrate))
        self._start_download(episode, quality, output_dir)

        self._set_normal_cursor()

    def start_download_episodes_multi(self, symbolic_quality, episodes,
                                      output_dir):
        self._set_wait_cursor()

        try:
            for episode in episodes:
                qualities = episode.get_available_qualities()
                if symbolic_quality == SymbolicQuality.HIGHEST:
                    quality = qualities[-1]
                elif symbolic_quality == SymbolicQuality.LOWEST:
                    quality = qualities[0]
                elif symbolic_quality == SymbolicQuality.AVERAGE:
                    avg = 0
                    for symbolic_quality in qualities:
                        avg += symbolic_quality.bitrate
                    avg /= len(qualities)
                    quality = min(qualities,
                                  key=lambda q: abs(q.bitrate - avg))

                tmpl = 'Queueing download of episode "{}" @ {} bps'
                logging.debug(tmpl.format(episode.get_title(), quality))
                self._start_download(episode, quality, output_dir)

        except exceptions.UnexpectedHttpStatusCodeError:
            self._error_msg_dialog.showMessage(
                'Could not download episode playlist. It might not be '
                'available yet.')
            return
        finally:
            self._set_normal_cursor()

    def _on_quality_chosen(self, quality, episodes):
        ''' user selected a quality from the popup '''
        logging.debug('Quality chosen')

        settings = self._app.get_settings()
        output_dir = settings.get_download_directory()
        if not os.path.isdir(output_dir):
            msg = 'Output directory "{}" does not exist'.format(output_dir)
            logging.error(msg)
            return

        if len(episodes) == 1:
            self.start_download_episode_single(
                quality, episodes[0], output_dir)
        elif len(episodes) > 1:
            self.start_download_episodes_multi(quality, episodes, output_dir)
