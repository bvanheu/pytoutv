import os.path
from PyQt4 import QtCore
from PyQt4 import QtGui
from toutvqt import utils
from toutvqt.settings import SettingsKeys


class QTouTvPreferencesDialog(utils.QCommonDialog, utils.QtUiLoad):
    _UI_NAME = 'preferences_dialog'
    settings_accepted = QtCore.pyqtSignal(dict)

    def __init__(self, settings):
        super().__init__()

        self._setup_ui()
        self._setup_signals()
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        dl_dir = settings.get_download_directory()
        proxy_url = settings.get_http_proxy()
        download_slots = settings.get_download_slots()
        always_max_quality = settings.get_always_max_quality()
        remove_finished = settings.get_remove_finished()

        self.http_proxy_value.setText(proxy_url)
        self.download_directory_value.setText(dl_dir)
        self.download_slots_value.setValue(download_slots)
        self.always_max_quality_check.setChecked(always_max_quality)
        self.remove_finished_check.setChecked(remove_finished)

    def _setup_signals(self):
        self.accepted.connect(self._send_settings_accepted)

    def _setup_ui(self):
        self._load_ui(QTouTvPreferencesDialog._UI_NAME)
        open_dl_dir_slot = self._open_download_directory_browser
        self.download_directory_browse.clicked.connect(open_dl_dir_slot)
        self._adjust_size()

    def _adjust_size(self):
        self.adjustSize()
        self.setFixedHeight(self.height())
        self.resize(600, self.height())

    def _open_download_directory_browser(self, checked):
        msg = 'Select download directory'
        dl_dir = QtGui.QFileDialog.getExistingDirectory(self, msg)
        if dl_dir.strip():
            self.download_directory_value.setText(os.path.abspath(dl_dir))

    def _send_settings_accepted(self):
        settings = {}

        dl_dir_value = self.download_directory_value.text().strip()
        proxy_url = self.http_proxy_value.text().strip()
        download_slots = self.download_slots_value.value()
        always_max_quality = self.always_max_quality_check.isChecked()
        remove_finished = self.remove_finished_check.isChecked()

        settings[SettingsKeys.NETWORK_HTTP_PROXY] = proxy_url
        settings[SettingsKeys.FILES_DOWNLOAD_DIR] = dl_dir_value
        settings[SettingsKeys.DL_DOWNLOAD_SLOTS] = download_slots
        settings[SettingsKeys.DL_ALWAYS_MAX_QUALITY] = always_max_quality
        settings[SettingsKeys.DL_REMOVE_FINISHED] = remove_finished

        self.settings_accepted.emit(settings)
