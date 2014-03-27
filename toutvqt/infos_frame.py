from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt
from PyQt4 import QtGui


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
        self._swap_infos_widget(self.emission_widget)

    def show_season(self, season):
        self._swap_infos_widget(self.season_widget)

    def show_episode(self, episode):
        self._swap_infos_widget(self.episode_widget)

    def _setup_none_label(self):
        self.none_label = Qt.QLabel()
        self.none_label.setText('Please select an item in the list above')
        font = Qt.QFont()
        font.setItalic(True)
        self.none_label.setFont(font)

    def _setup_infos_widget(self):
        self.emission_widget = QEmissionWidget()
        self.season_widget = QSeasonWidget()
        self.episode_widget = QEpisodeWidget()

    def _setup_ui(self):
        self.setLayout(Qt.QVBoxLayout())
        self.setFrameShape(Qt.QFrame.Box)
        self.setFrameShadow(Qt.QFrame.Sunken)
        self._setup_none_label()
        self._setup_infos_widget()
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)


class QEmissionWidget(Qt.QWidget):
        UI_PATH = resource_filename(
            __name__, 'dat/ui/infos_emission_widget.ui')

        def __init__(self):
                super(QEmissionWidget, self).__init__()
                self._setup_ui()

        def _setup_ui(self):
                uic.loadUi(QEmissionWidget.UI_PATH, baseinstance=self)


class QSeasonWidget(Qt.QWidget):
        UI_PATH = resource_filename(__name__, 'dat/ui/infos_season_widget.ui')

        def __init__(self):
                super(QSeasonWidget, self).__init__()
                self._setup_ui()

        def _setup_ui(self):
                uic.loadUi(QSeasonWidget.UI_PATH, baseinstance=self)


class QEpisodeWidget(Qt.QWidget):
        UI_PATH = resource_filename(__name__, 'dat/ui/infos_episode_widget.ui')

        def __init__(self):
                super(QEpisodeWidget, self).__init__()
                self._setup_ui()

        def _setup_ui(self):
                uic.loadUi(QEpisodeWidget.UI_PATH, baseinstance=self)
