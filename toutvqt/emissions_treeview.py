from pkg_resources import resource_filename
from PyQt4 import Qt, QtCore
from toutvqt.emissions_treemodel import EmissionsTreeModelEmission, EmissionsTreeModelEpisode, EmissionsTreeModelSeason
from toutvqt.emissions_treemodel import FakeDataSource


class QEmissionsTreeView(Qt.QTreeView):
    def __init__(self, model):
        super(QEmissionsTreeView, self).__init__()

        self._setup(model)

    emission_selected = QtCore.pyqtSignal(object)
    season_selected = QtCore.pyqtSignal(object)
    episode_selected = QtCore.pyqtSignal(object)
    none_selected = QtCore.pyqtSignal()

    def _setup(self, model):
        #xml_path = resource_filename(__name__, 'dat/fakedata.xml')
        #data = FakeDataSource(xml_path)
        #model = EmissionsTreeModel(data)
        self.setModel(model)
        self.expanded.connect(model.item_expanded)

        selection_model = Qt.QItemSelectionModel(model)
        self.setSelectionModel(selection_model)

        selection_model.selectionChanged.connect(self.item_selection_changed)

    def item_selection_changed(self, selected, deselected):
        # TODO: We should send something useful with the signals.
        indexes = selected.indexes()

        if len(indexes) == 0:
            self.none_selected.emit()
            return

        index = indexes[0]
        item = index.internalPointer()
        if type(item) == EmissionsTreeModelEmission:
            self.emission_selected.emit(None)
        elif type(item) == EmissionsTreeModelSeason:
            self.season_selected.emit(None)
        elif type(item) == EmissionsTreeModelEpisode:
            self.episode_selected.emit(None)
        else:
            self.none_selected.emit()
