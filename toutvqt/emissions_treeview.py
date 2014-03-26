from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore
from toutvqt.emissions_treemodel import EmissionsTreeModel, EmissionsTreeModelEmission, EmissionsTreeModelEpisode, EmissionsTreeModelSeason
from toutvqt.emissions_treemodel import FakeDataSource


class QEmissionsTreeView(Qt.QTreeView):
    def __init__(self):
        super(QEmissionsTreeView, self).__init__()

        self._setup()

    emission_selected = QtCore.pyqtSignal(object)
    season_selected = QtCore.pyqtSignal(object)
    episode_selected = QtCore.pyqtSignal(object)

    def _setup(self):
        xml_path = resource_filename(__name__, 'dat/fakedata.xml')
        data = FakeDataSource(xml_path)
        model = EmissionsTreeModel(data)
        self.setModel(model)
        self.expanded.connect(model.item_expanded)

        selection_model = Qt.QItemSelectionModel(model)
        self.setSelectionModel(selection_model)

        selection_model.selectionChanged.connect(self.item_selection_changed)

    def item_selection_changed(self, selected, deselected):
        # TODO: We should send something useful with the signals.
        indexes = selected.indexes()

        if len(indexes) == 0:
            return

        index = indexes[0]
        item = index.internalPointer()
        if type(item) == EmissionsTreeModelEmission:
            self.emission_selected.emit(None)
        elif type(item) == EmissionsTreeModelSeason:
            self.season_selected.emit(None)
        elif type(item) == EmissionsTreeModelEpisode:
            self.episode_selected.emit(None)
