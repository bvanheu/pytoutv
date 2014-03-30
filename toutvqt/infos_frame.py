from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore
import webbrowser
from toutvqt.choose_bitrate_dialog import QChooseBitrateDialog


class QInfosFrame(Qt.QFrame):
    def __init__(self):
        super(QInfosFrame, self).__init__()

        self._setup_ui()
        self.show_infos_none()

    def _swap_infos_widget(self, widget):
        for swappable_widget in self._swappable_widgets:
            if widget is not swappable_widget:
                swappable_widget.hide()
        widget.show()

    def exit(self):
        self.episode_widget.exit()

    def show_infos_none(self):
        self._swap_infos_widget(self.none_label)

    def show_emission(self, emission):
        self.emission_widget.set_emission(emission)
        self._swap_infos_widget(self.emission_widget)

    def show_season(self, emission, season_number, episodes):
        self.season_widget.set_infos(emission, season_number, episodes)
        self._swap_infos_widget(self.season_widget)

    def show_episode(self, episode):
        self.episode_widget.set_episode(episode)
        self._swap_infos_widget(self.episode_widget)

    def _setup_none_label(self):
        self.none_label = Qt.QLabel()
        self.none_label.setText('Please select an item in the list above')
        font = Qt.QFont()
        font.setItalic(True)
        self.none_label.setFont(font)

    def _setup_infos_widget(self):
        self._setup_none_label()
        self.emission_widget = QEmissionInfosWidget()
        self.season_widget = QSeasonInfosWidget()
        self.episode_widget = QEpisodeInfosWidget()

        self._swappable_widgets = [
            self.emission_widget,
            self.season_widget,
            self.episode_widget,
            self.none_label,
        ]

        for widget in self._swappable_widgets:
            widget.hide()
            self.layout().addWidget(widget)

    def _setup_ui(self):
        self.setLayout(Qt.QVBoxLayout())
        self.setFrameShape(Qt.QFrame.Box)
        self.setFrameShadow(Qt.QFrame.Sunken)
        self._setup_infos_widget()
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Maximum)


class QInfosWidget(Qt.QWidget):
    def __init__(self):
        super(QInfosWidget, self).__init__()

        self._url = None

    def _setup_ui(self, ui_path):
        uic.loadUi(ui_path, baseinstance=self)
        self.goto_toutv_btn.clicked.connect(self._on_goto_toutv_btn_clicked)
        self.dl_btn.clicked.connect(self._on_dl_btn_clicked)

    def _set_toutv_url(self, url):
        self._url = url
        if url is None:
            self.goto_toutv_btn.hide()
        else:
            self.goto_toutv_btn.show()

    def _on_goto_toutv_btn_clicked(self):
        if self._url is not None:
            webbrowser.open(self._url)

    def _on_dl_btn_clicked(self):
        pass


class QEmissionCommonInfosWidget:
    def _set_removal_date(self):
        removal_date = self._emission.get_removal_date()
        if removal_date is None:
            removal_date = '-'
        else:
            removal_date = str(removal_date)
        self.removal_date_value_label.setText(removal_date)

    def _set_genre(self):
        genre = self._emission.get_genre()
        if genre is None:
            genre = '-'
        else:
            genre = genre.get_title()
        self.genre_value_label.setText(genre)

    def _set_network(self):
        network = self._emission.get_network()
        if network is None:
            network = '-'
        self.network_value_label.setText(network)

    def _set_country(self):
        country = self._emission.get_country()
        if country is None:
            country = '-'
        self.country_value_label.setText(country)

    def _set_common_infos(self):
        self._set_removal_date()
        self._set_genre()
        self._set_network()
        self._set_country()


class QEmissionInfosWidget(QInfosWidget, QEmissionCommonInfosWidget):
    _UI_PATH = resource_filename(__name__, 'dat/ui/emission_infos_widget.ui')

    def __init__(self):
        super(QEmissionInfosWidget, self).__init__()

        self._setup_ui(QEmissionInfosWidget._UI_PATH)

    def _set_title(self):
        self.title_value_label.setText(self._emission.get_title())

    def _set_description(self):
        description = self._emission.get_description()
        if description is None:
            description = ''
        self.description_value_label.setText(description)

    def set_emission(self, emission):
        self._emission = emission

        self._set_title()
        self._set_description()
        self._set_common_infos()
        self._set_toutv_url(emission.get_url())


class QSeasonInfosWidget(QInfosWidget, QEmissionCommonInfosWidget):
    _UI_PATH = resource_filename(__name__, 'dat/ui/season_infos_widget.ui')

    def __init__(self):
        super(QSeasonInfosWidget, self).__init__()

        self._setup_ui(QSeasonInfosWidget._UI_PATH)

    def _set_season_number(self):
        self.season_number_value_label.setText(str(self._season_number))

    def _set_number_episodes(self):
        self.number_episodes_value_label.setText(str(len(self._episodes)))

    def set_infos(self, emission, season_number, episodes):
        self._emission = emission
        self._season_number = season_number
        self._episodes = episodes

        self._set_season_number()
        self._set_number_episodes()
        self._set_common_infos()
        self._set_toutv_url(emission.get_url())


class QEpisodeInfosWidget(QInfosWidget):
    _UI_PATH = resource_filename(__name__, 'dat/ui/episode_infos_widget.ui')
    _fetch_thumb_required = QtCore.pyqtSignal(object)

    def __init__(self):
        super(QEpisodeInfosWidget, self).__init__()

        self._episode = None

        self._setup_ui(QEpisodeInfosWidget._UI_PATH)
        self._setup_thumb_fetching();

    def exit(self):
        self._fetch_thumb_thread.quit()
        self._fetch_thumb_thread.wait()

    def _setup_ui(self, ui_path):
        super(QEpisodeInfosWidget, self)._setup_ui(ui_path)
        width = self.thumb_value_label.width()
        min_height = round(width * 9 / 16) + 1
        self.thumb_value_label.setMinimumHeight(min_height)

    def _setup_thumb_fetching(self):
        # Setup fetch thread and signal connections
        self._fetch_thumb_thread = Qt.QThread()
        self._fetch_thumb_thread.start()

        self._thumb_fetcher = QEpisodeThumbFetcher()
        self._thumb_fetcher.moveToThread(self._fetch_thumb_thread)
        self._fetch_thumb_required.connect(self._thumb_fetcher.fetch_thumb)
        self._thumb_fetcher.fetch_done.connect(self._thumb_fetched)

    def _thumb_fetched(self, episode):
        if episode is not self._episode:
            # Ignore; next time will be faster anyway
            self._set_no_thumb()
            return

        self._set_thumb()

    def _set_description(self):
        description = self._episode.get_description()
        if description is None:
            description = '-'
        self.description_value_label.setText(description)

    def _set_air_date(self):
        air_date = self._episode.get_air_date()
        if air_date is None:
            air_date = '-'
        self.air_date_value_label.setText(str(air_date))

    def _set_length(self):
        minutes, seconds = self._episode.get_length()
        length = '{}:{:02}'.format(minutes, seconds)
        self.length_value_label.setText(length)

    def _set_sae(self):
        sae = self._episode.get_sae()
        if sae is None:
            sae = '-'
        self.sae_value_label.setText(sae)

    def _set_director(self):
        director = self._episode.get_director()
        if director is None:
            director = '-'
        self.director_value_label.setText(director)

    def _set_author(self):
        author = self._episode.get_author()
        if author is None:
            author = '-'
        self.author_value_label.setText(author)

    def _set_titles(self):
        emission = self._episode.get_emission()
        self.title_value_label.setText(self._episode.get_title())
        self.emission_title_value_label.setText(emission.get_title())

    def _set_no_thumb(self):
        self.thumb_value_label.setPixmap(Qt.QPixmap())

    def _set_thumb(self):
        jpeg_data = self._episode.get_medium_thumb_data()
        if jpeg_data is None:
            self._set_no_thumb()

        pixmap = Qt.QPixmap()
        ret = pixmap.loadFromData(jpeg_data, 'JPEG')
        if not ret:
            self._set_no_thumb()

        smooth_transform = QtCore.Qt.SmoothTransformation
        width = self.thumb_value_label.width()
        scaled_pixmap = pixmap.scaledToWidth(width, smooth_transform)
        self.thumb_value_label.setPixmap(pixmap)

    def _try_set_thumb(self):
        if self._episode.has_medium_thumb_data():
            self._set_thumb()
        else:
            self._set_no_thumb()
            self._fetch_thumb_required.emit(self._episode)

    def set_episode(self, episode):
        self._episode = episode

        self._set_titles()
        self._set_author()
        self._set_director()
        self._set_description()
        self._set_air_date()
        self._set_length()
        self._set_sae()
        self._try_set_thumb()
        url = '{}?autoplay=true'.format(episode.get_url())
        self._set_toutv_url(url)

    def _on_bitrate_chosen(self, bitrate):
        print('chose {} bps'.format(bitrate))

    def _on_dl_btn_clicked(self):
        pos = QtGui.QCursor().pos()
        cursor = self.dl_btn.cursor()
        self.dl_btn.setCursor(QtCore.Qt.WaitCursor)
        bitrates = self._episode.get_available_bitrates()
        self.dl_btn.setCursor(cursor)
        if len(bitrates) > 1:
            dialog = QChooseBitrateDialog(bitrates)
            dialog.bitrate_chosen.connect(self._on_bitrate_chosen)
            pos.setX(pos.x() - dialog.width())
            pos.setY(pos.y() - dialog.height())
            dialog.show_move(pos)
        else:
            print('single bitrate: {}'.format(bitrate[0]))


class QEpisodeThumbFetcher(Qt.QObject):
    fetch_done = QtCore.pyqtSignal(object)

    def __init__(self):
        super(QEpisodeThumbFetcher, self).__init__()

    def fetch_thumb(self, episode):
        episode.get_medium_thumb_data()
        self.fetch_done.emit(episode)
