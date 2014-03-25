from pkg_resources import resource_filename
from PyQt4 import Qt
from toutvqt.emissions_treemodel import EmissionsTreeModel
from toutvqt.emissions_treemodel import FakeDataSource


class QEmissionsTreeView(Qt.QTreeView):
    def __init__(self):
        super(QEmissionsTreeView, self).__init__()

        self._setup()

    def _setup(self):
        xml_path = resource_filename(__name__, 'dat/fakedata.xml')
        data = FakeDataSource(xml_path)
        model = EmissionsTreeModel(data)
        self.setModel(model)
        self.expanded.connect(model.item_expanded)
