from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4 import QtGui
import webbrowser


class QInfosFrame(Qt.QFrame):
    def __init__(self):
        super(QInfosFrame, self).__init__()

        self._setup_ui()
        self.show_infos_none()

    def _swap_infos_widget(self, widget):
        layout = self.layout()

        if layout.count() == 1:
            cur_widget = layout.itemAt(0).widget()
            cur_widget.setParent(None)
        layout.addWidget(widget)

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
        self.emission_widget = QEmissionInfosWidget()
        self.season_widget = QSeasonInfosWidget()
        self.episode_widget = QEpisodeInfosWidget()

    def _setup_ui(self):
        self.setLayout(Qt.QVBoxLayout())
        self.setFrameShape(Qt.QFrame.Box)
        self.setFrameShadow(Qt.QFrame.Sunken)
        self._setup_none_label()
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

    def _set_toutv_url(self, url):
        self._url = url
        if url is None:
            self.goto_toutv_btn.hide()
        else:
            self.goto_toutv_btn.show()

    def _on_goto_toutv_btn_clicked(self):
        if self._url is not None:
            webbrowser.open(self._url)


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
    UI_PATH = resource_filename(__name__, 'dat/ui/emission_infos_widget.ui')

    def __init__(self):
        super(QEmissionInfosWidget, self).__init__()

        self._setup_ui(QEmissionInfosWidget.UI_PATH)

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
    UI_PATH = resource_filename(__name__, 'dat/ui/season_infos_widget.ui')

    def __init__(self):
        super(QSeasonInfosWidget, self).__init__()

        self._setup_ui(QSeasonInfosWidget.UI_PATH)

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
        self._set_common_infos(emission)
        self._set_toutv_url(emission.get_url())


class QEpisodeInfosWidget(QInfosWidget):
    UI_PATH = resource_filename(__name__, 'dat/ui/episode_infos_widget.ui')

    def __init__(self):
        super(QEpisodeInfosWidget, self).__init__()

        self._setup_ui(QEpisodeInfosWidget.UI_PATH)

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

    def _set_titles(self):
        emission = self._episode.get_emission()
        self.title_value_label.setText(self._episode.get_title())
        self.emission_title_value_label.setText(emission.get_title())

    def set_episode(self, episode):
        self._episode = episode

        self._set_titles()
        self._set_description()
        self._set_air_date()
        self._set_length()
        self._set_sae()
        self._set_toutv_url(episode.get_url())
