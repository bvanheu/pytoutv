import logging
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore
import webbrowser
from toutvqt import utils


class QInfosFrame(Qt.QFrame):
    select_download = QtCore.pyqtSignal(list)

    def __init__(self, client):
        super().__init__()

        self._client = client

        self._setup_thumb_fetching()
        self._setup_ui()
        self.show_infos_none()

    def _swap_infos_widget(self, widget):
        for swappable_widget in self._swappable_widgets:
            if widget is not swappable_widget:
                swappable_widget.hide()
        widget.show()

    def exit(self):
        logging.debug('Joining thumb fetcher thread')
        self._fetch_thumb_thread.quit()
        self._fetch_thumb_thread.wait()

    def show_infos_none(self):
        logging.debug('Showing none label')
        self._swap_infos_widget(self.none_label)

    def show_emission(self, emission):
        logging.debug('Showing emission infos')
        self.emission_widget.set_emission(emission)
        self._swap_infos_widget(self.emission_widget)

    def show_season(self, emission, season_number, episodes):
        logging.debug('Showing season infos')
        self.season_widget.set_infos(emission, season_number, episodes)
        self._swap_infos_widget(self.season_widget)

    def show_episode(self, episode):
        logging.debug('Showing episode infos')
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
        self.emission_widget = _QEmissionInfosWidget(self._thumb_fetcher,
                                                     self._client)
        self.emission_widget.select_download.connect(self.select_download)
        self.season_widget = _QSeasonInfosWidget()
        self.season_widget.select_download.connect(self.select_download)
        self.episode_widget = _QEpisodeInfosWidget(self._thumb_fetcher)
        self.episode_widget.select_download.connect(self.select_download)

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

    def _setup_thumb_fetching(self):
        self._fetch_thumb_thread = Qt.QThread()
        self._fetch_thumb_thread.start()

        self._thumb_fetcher = _QThumbFetcher()
        self._thumb_fetcher.moveToThread(self._fetch_thumb_thread)


class _QThumbFetcher(Qt.QObject):
    fetch_done = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self._last = None

    def set_last(self, bo):
        self._last = bo

    def fetch_thumb(self, bo):
        if bo is not self._last:
            tmpl = 'Skipping thumbnail fetching of "{}"'
            logging.debug(tmpl.format(bo.get_title()))
            return

        tmpl = 'Fetching thumbnail for episode "{}"'
        logging.debug(tmpl.format(bo.get_title()))
        bo.get_medium_thumb_data()
        self.fetch_done.emit(bo)


class _QInfosWidget(Qt.QWidget, utils.QtUiLoad):
    _fetch_thumb_required = QtCore.pyqtSignal(object)
    select_download = QtCore.pyqtSignal(object)

    def __init__(self, thumb_fetcher):
        super().__init__()

        self._thumb_fetcher = thumb_fetcher
        self._bo = None
        self._url = None

    def _setup_ui(self, ui_name):
        self._load_ui(ui_name)
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
            logging.debug('Going to TOU.TV @ "{}"'.format(self._url))
            webbrowser.open(self._url)

    def _on_dl_btn_clicked(self):
        logging.debug('Download button clicked')
        pass

    def _setup_thumb_fetching(self):
        # Setup signal connections with thumb fetcher
        self._fetch_thumb_required.connect(self._thumb_fetcher.fetch_thumb)
        self._thumb_fetcher.fetch_done.connect(self._thumb_fetched)

    def _set_no_thumb(self):
        self.thumb_value_label.setPixmap(Qt.QPixmap())

    def _set_thumb(self):
        jpeg_data = self._bo.get_medium_thumb_data()
        if jpeg_data is None:
            self._set_no_thumb()

        pixmap = Qt.QPixmap()
        ret = pixmap.loadFromData(jpeg_data, 'JPEG')
        if not ret:
            self._set_no_thumb()
            return

        smooth_transform = QtCore.Qt.SmoothTransformation
        width = self.thumb_value_label.width()
        scaled_pixmap = pixmap.scaledToWidth(width, smooth_transform)
        self.thumb_value_label.setPixmap(scaled_pixmap)

    def _try_set_thumb(self):
        if self._bo.has_medium_thumb_data():
            self._set_thumb()
        else:
            self._set_no_thumb()
            self._thumb_fetcher.set_last(self._bo)
            self._fetch_thumb_required.emit(self._bo)

    def _thumb_fetched(self, bo):
        if bo is not self._bo:
            # Not us, or too late. Ignore; next time will be faster anyway.
            return

        self._set_thumb()


class _QEmissionCommonInfosWidget:
    def _set_removal_date(self):
        removal_date = self._bo.get_removal_date()
        if removal_date is None:
            removal_date = '-'
        else:
            removal_date = str(removal_date)
        self.removal_date_value_label.setText(removal_date)

    def _set_genre(self):
        genre = self._bo.get_genre()
        if genre is None:
            genre = '-'
        else:
            genre = genre.get_title()
        self.genre_value_label.setText(genre)

    def _set_network(self):
        network = self._bo.get_network()
        if network is None:
            network = '-'
        self.network_value_label.setText(network)

    def _set_country(self):
        country = self._bo.get_country()
        if country is None:
            country = '-'
        self.country_value_label.setText(country)

    def _set_common_infos(self):
        self._set_removal_date()
        self._set_genre()
        self._set_network()
        self._set_country()


class _QEmissionInfosWidget(_QInfosWidget, _QEmissionCommonInfosWidget):
    _UI_NAME = 'emission_infos_widget'
    _fetch_thumb_required = QtCore.pyqtSignal(object)

    def __init__(self, thumb_fetcher, client):
        super().__init__(thumb_fetcher)

        self._client = client

        self._setup_ui(_QEmissionInfosWidget._UI_NAME)
        self._setup_thumb_fetching()

    def _setup_ui(self, ui_name):
        super()._setup_ui(ui_name)
        width = self.thumb_value_label.width()
        min_height = round(width * 9 / 16) + 1
        self.thumb_value_label.setMinimumHeight(min_height)

    def _set_title(self):
        self.title_value_label.setText(self._bo.get_title())

    def _set_description(self):
        description = self._bo.get_description()
        if description is None:
            description = ''
        self.description_value_label.setText(description)

    def set_emission(self, emission):
        self._bo = emission

        self._set_title()
        self._set_description()
        self._set_common_infos()
        self._set_toutv_url(emission.get_url())
        self._try_set_thumb()

    def _on_dl_btn_clicked(self):
        episodes = self._client.get_emission_episodes(self._bo)
        self.select_download.emit(list(episodes))


class _QSeasonInfosWidget(_QInfosWidget, _QEmissionCommonInfosWidget):
    _UI_NAME = 'season_infos_widget'

    def __init__(self):
        super().__init__(None)

        self._setup_ui(_QSeasonInfosWidget._UI_NAME)

    def _set_season_number(self):
        self.season_number_value_label.setText(str(self._season_number))

    def _set_number_episodes(self):
        self.number_episodes_value_label.setText(str(len(self._episodes)))

    def set_infos(self, emission, season_number, episodes):
        self._bo = emission
        self._season_number = season_number
        self._episodes = [e.bo for e in episodes]

        self._set_season_number()
        self._set_number_episodes()
        self._set_common_infos()
        self._set_toutv_url(emission.get_url())

    def _on_dl_btn_clicked(self):
        self.select_download.emit(self._episodes)


class _QEpisodeInfosWidget(_QInfosWidget):
    _UI_NAME = 'episode_infos_widget'

    def __init__(self, thumb_fetcher):
        super().__init__(thumb_fetcher)

        self._setup_ui(_QEpisodeInfosWidget._UI_NAME)
        self._setup_thumb_fetching()

    def _setup_ui(self, ui_name):
        super()._setup_ui(ui_name)
        width = self.thumb_value_label.width()
        min_height = round(width * 9 / 16) + 1
        self.thumb_value_label.setMinimumHeight(min_height)

    def _set_description(self):
        description = self._bo.get_description()
        if description is None:
            description = '-'
        self.description_value_label.setText(description)

    def _set_air_date(self):
        air_date = self._bo.get_air_date()
        if air_date is None:
            air_date = '-'
        self.air_date_value_label.setText(str(air_date))

    def _set_length(self):
        minutes, seconds = self._bo.get_length()
        length = '{}:{:02}'.format(minutes, seconds)
        self.length_value_label.setText(length)

    def _set_sae(self):
        sae = self._bo.get_sae()
        if sae is None:
            sae = '-'
        self.sae_value_label.setText(sae)

    def _set_director(self):
        director = self._bo.get_director()
        if director is None:
            director = '-'
        self.director_value_label.setText(director)

    def _set_author(self):
        author = self._bo.get_author()
        if author is None:
            author = '-'
        self.author_value_label.setText(author)

    def _set_titles(self):
        emission = self._bo.get_emission()
        self.title_value_label.setText(self._bo.get_title())
        self.emission_title_value_label.setText(emission.get_title())

    def set_episode(self, episode):
        self._bo = episode

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

    def _on_dl_btn_clicked(self):
        self.select_download.emit([self._bo])
