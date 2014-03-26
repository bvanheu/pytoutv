from pkg_resources import resource_filename
from PyQt4 import uic
from PyQt4 import Qt


class QInfosFrame(Qt.QFrame):
    def __init__(self):
        super(QInfosFrame, self).__init__()

        self._setup_ui()
        self.show_infos_none()

    def _swap_infos_widget(self, widget):
        layout = self.layout()

        if layout.count() == 1:
            layout.takeAt(0)
        layout.addWidget(widget)

    def show_infos_none(self):
        self._swap_infos_widget(self.none_label)

    def show_emission(self, emission):
        print("Selected emission")
        self._swap_infos_widget(self.emissions_widget)

    def show_season(self, season):
        print("Selected season")

    def show_episode(self, episode):
        print("Selected episode")

    def _setup_none_label(self):
        self.none_label = Qt.QLabel()
        self.none_label.setText('Please select an item in the list above')
        font = Qt.QFont()
        font.setItalic(True)
        self.none_label.setFont(font)

    def _setup_emissions_widget(self):
        self.emissions_widget = QEmissionsWidget()

    def _setup_ui(self):
        self.setLayout(Qt.QVBoxLayout())
        self.setFrameShape(Qt.QFrame.Box)
        self.setFrameShadow(Qt.QFrame.Sunken)
        self._setup_none_label()
        self._setup_emissions_widget()


class QEmissionsWidget(Qt.QWidget):
        UI_PATH = resource_filename(__name__, 'dat/ui/infos_emission_widget.ui')

        def __init__(self):
                super(QEmissionsWidget, self).__init__()
                self._setup_ui()

        def _setup_ui(self):
                uic.loadUi(QEmissionsWidget.UI_PATH, baseinstance=self)
