import logging
from PyQt4 import Qt, QtCore
from toutvqt.emissions_treemodel import EmissionsTreeModelEmission
from toutvqt.emissions_treemodel import EmissionsTreeModelSeason
from toutvqt.emissions_treemodel import EmissionsTreeModelEpisode
from toutvqt.emissions_treemodel import LoadingItem


class QEmissionsTreeViewStyleDelegate(Qt.QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        if type(index.internalPointer()) is LoadingItem:
            option.font.setItalic(True)
        Qt.QStyledItemDelegate.paint(self, painter, option, index)


class QEmissionsTreeView(Qt.QTreeView):
    emission_selected = QtCore.pyqtSignal(object)
    season_selected = QtCore.pyqtSignal(object, int, list)
    episode_selected = QtCore.pyqtSignal(object)
    none_selected = QtCore.pyqtSignal()

    def __init__(self, model):
        super().__init__()

        self._setup(model)

    def _setup(self, model):
        self.setModel(model)
        self.expanded.connect(model.item_expanded)

        selection_model = Qt.QItemSelectionModel(model)
        self.setSelectionModel(selection_model)

        self.setItemDelegate(QEmissionsTreeViewStyleDelegate())

        selection_model.selectionChanged.connect(self.item_selection_changed)

        model.fetching_start.connect(self._on_fetch_start)
        model.fetching_done.connect(self._on_fetch_done)

    def _on_fetch_start(self):
        self.setCursor(QtCore.Qt.WaitCursor)

    def _on_fetch_done(self):
        self.setCursor(QtCore.Qt.ArrowCursor)

    def set_default_columns_widths(self):
        self.setColumnWidth(0, self.width() - 300)
        self.setColumnWidth(1, 100)

    def item_selection_changed(self, selected, deselected):
        logging.debug('Treeview item selection changed')

        indexes = selected.indexes()

        if not indexes:
            self.none_selected.emit()
            return

        index = indexes[0]
        item = index.internalPointer()
        if type(item) == EmissionsTreeModelEmission:
            self.emission_selected.emit(item.bo)
        elif type(item) == EmissionsTreeModelSeason:
            self.season_selected.emit(item.emission.bo, item.number,
                                      item.episodes)
        elif type(item) == EmissionsTreeModelEpisode:
            self.episode_selected.emit(item.bo)
        else:
            self.none_selected.emit()
