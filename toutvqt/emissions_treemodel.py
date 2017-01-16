from PyQt4 import Qt
from PyQt4 import QtCore
import logging
import re
import toutv.client


class FetchState:
    NOPE = 0
    STARTED = 1
    DONE = 2


class LoadingItem:
    def __init__(self, my_parent):
        self.my_parent = my_parent

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return 'Loading...'
            else:
                return ''

    def rowCount(self):
        # The Loading item does not have any child.
        return 0

    def index(self, row, column, createIndex):
        logging.error('Internal error: index() called on LoadingItem')

        return Qt.QModelIndex()

    def parent(self, child, createIndex):
        if self.my_parent is not None:
            return createIndex(0, 0, self.my_parent)
        else:
            return Qt.QModelIndex()


class EmissionsTreeModelEmission:
    def __init__(self, emission_bo, row_in_parent):
        self.bo = emission_bo
        self.seasons = []
        self.loading_item = LoadingItem(self)
        self.row_in_parent = row_in_parent
        self.fetched = FetchState.NOPE

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self.bo.get_title()
            elif column == 1:
                network = self.bo.get_network()
                if network is None:
                    network = ''
                return network
            return ''

    def rowCount(self):
        if self.fetched == FetchState.DONE:
            return len(self.seasons)
        else:
            # The "Loading" item
            return 1

    def index(self, row, column, createIndex):
        if self.fetched == FetchState.DONE:
            return createIndex(row, column, self.seasons[row])
        else:
            return createIndex(row, column, self.loading_item)

    def parent(self, child, createIndex):
        # An emission is at root level
        return Qt.QModelIndex()

    def should_fetch(self):
        return self.fetched == FetchState.NOPE

    def set_children(self, c):
        self.seasons = c


class EmissionsTreeModelSeason:
    def __init__(self, number, row_in_parent):
        self.number = number
        self.episodes = []
        self.row_in_parent = row_in_parent

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return 'S{:02}'.format(self.number)
            elif column == 1:
                network = self.emission.bo.get_network()
                if network is None:
                    network = ''

                return network

            return ''

    def rowCount(self):
        return len(self.episodes)

    def index(self, row, column, createIndex):
        return createIndex(row, column, self.episodes[row])

    def should_fetch(self):
        return False

    def parent(self, child, createIndex):
        return createIndex(self.row_in_parent, 0, self.emission)


class EmissionsTreeModelEpisode:
    def __init__(self, bo, row_in_parent):
        self.bo = bo
        self.loading_item = LoadingItem(self)
        self.row_in_parent = row_in_parent

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self.bo.get_title()
            elif column == 1:
                emission = self.bo.get_emission()
                network = emission.get_network()
                if network is None:
                    network = ''

                return network
            elif column == 2:
                episode_number = self.bo.get_episode_number()
                if episode_number is not None:
                    return episode_number

                return ''

            return '?'

    def rowCount(self):
        # An episode does not have any child
        return 0

    def index(self, row, column, createIndex):
        msg = 'Internal error: index() called on EmissionsTreeModelEpisode'
        logging.error(msg)
        return Qt.QModelIndex()

    def parent(self, child, createIndex):
        return createIndex(self.row_in_parent, 0, self.season)


class EmissionsTreeModel(Qt.QAbstractItemModel):
    _HEADER = [
        'Title',
        'Network',
        'Episode number',
    ]
    fetch_required = QtCore.pyqtSignal(object)
    fetching_start = QtCore.pyqtSignal()
    fetching_done = QtCore.pyqtSignal()

    def __init__(self, client):
        super().__init__()
        self.emissions = []
        self.loading_item = LoadingItem(None)

        # Have we fetched the emissions?
        self.fetched = FetchState.NOPE

        # Setup fetch thread and signal connections
        self.fetch_thread = Qt.QThread()
        self.fetch_thread.start()

        self.fetcher = EmissionsTreeModelFetcher(client)
        self.fetcher.moveToThread(self.fetch_thread)
        self.fetch_required.connect(self.fetcher.new_work_piece)
        self.fetcher.fetch_done.connect(self.fetch_done)
        self.fetcher.fetch_error.connect(self.fetch_error)
        self.modelAboutToBeReset.connect(self._on_about_to_reset)
        self.modelReset.connect(self._on_model_reset)

    def exit(self):
        logging.debug('Joining tree model fetch thread')
        self.fetch_thread.quit()
        self.fetch_thread.wait()

    def index(self, row, column, parent=Qt.QModelIndex()):
        """Returns a QModelIndex to represent a cell of a child of parent."""
        if not parent.isValid():
            # Create an index for a emission
            if self.fetched == FetchState.DONE:
                emission = self.emissions[row]
                return self.createIndex(row, column, emission)
            else:
                return self.createIndex(row, column, self.loading_item)
        else:
            return parent.internalPointer().index(row, column,
                                                  self.createIndex)

    def parent(self, child):
        item = child.internalPointer()
        return item.parent(child, self.createIndex)

    def rowCount(self, parent=Qt.QModelIndex()):
        if not parent.isValid():
            if self.fetched == FetchState.DONE:
                return len(self.emissions)
            else:
                # The "Loading" item
                return 1
        else:
            return parent.internalPointer().rowCount()

    def columnCount(self, parent=Qt.QModelIndex()):
        return len(self._HEADER)

    def fetch_done(self, parent, children_list):
        """A fetch work is complete."""

        # Remove the "Loading"
        self.beginRemoveRows(parent, 0, 0)
        if parent.isValid():
            parent.internalPointer().fetched = FetchState.DONE
        else:
            self.fetched = FetchState.DONE
        self.endRemoveRows()

        # Add the actual children
        self.beginInsertRows(parent, 0, len(children_list) - 1)
        if parent.isValid():
            parent.internalPointer().set_children(children_list)
        else:
            self.emissions = children_list
        self.endInsertRows()

        self.fetching_done.emit()

    def fetch_error(self, parent, ex):
        if type(ex) is toutv.client.ClientError:
            # msg = 'Client error: {}'.format(ex)
            pass
        else:
            logging.error('Error: {}'.format(ex))

        self.fetching_done.emit()

    def init_fetch(self, parent=Qt.QModelIndex()):
        logging.debug('Initializing emissions fetching')

        if parent.isValid():
            parent.internalPointer().fetched = FetchState.STARTED
        else:
            self.fetched = FetchState.STARTED

        parent = Qt.QModelIndex(parent)
        self.fetch_required.emit(parent)
        self.fetching_start.emit()

    def item_expanded(self, parent):
        """Slot called when an item in the tree has been expanded."""
        if parent.internalPointer().should_fetch():
            self.init_fetch(parent)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        return index.internalPointer().data(index, role)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return EmissionsTreeModel._HEADER[section]

    def _on_about_to_reset(self):
        if self.fetched == FetchState.DONE:
            self.emissions = []
            self.fetched = FetchState.NOPE

    def _on_model_reset(self):
        if self.fetched == FetchState.NOPE:
            self.init_fetch()


class EmissionsTreeModelFetcher(Qt.QObject):
    fetch_done = QtCore.pyqtSignal(object, list)
    fetch_error = QtCore.pyqtSignal(object, object)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def new_work_piece(self, parent):
        if not parent.isValid():
            self.fetch_emissions(parent)
        elif type(parent.internalPointer()) == EmissionsTreeModelEmission:
            self.fetch_seasons(parent)
        elif type(parent.internalPointer()) == EmissionsTreeModelSeason:
            self.fetch_episodes(parent)

    def fetch_emissions(self, parent):
        def key_func(ekey):
            # Cheap and easy way to sort latin titles (which is the case here)
            emission_title = emissions[ekey].get_title()
            reps = [
                ('[àáâä]', 'a'),
                ('[ÀÁÂÄ]', 'A'),
                ('[éèêë]', 'e'),
                ('[ÉÈÊË]', 'E'),
                ('[íìîï]', 'i'),
                ('[ÍÌÎÏ]', 'I'),
                ('[óòôö]', 'o'),
                ('[ÓÒÔÖ]', 'O'),
                ('[úùûü]', 'u'),
                ('[ÚÙÛÜ]', 'U'),
                ('ç', 'c'),
                ('Ç', 'C'),
            ]
            for regex, rep in reps:
                emission_title = re.sub(regex, rep, emission_title)

            return emission_title.lower()

        logging.debug('Fetching emissions')

        try:
            emissions = self.client.get_page_repertoire().get_emissions()
        except Exception as e:
            self.fetch_error.emit(parent, e)
            return

        # Sort
        emissions_keys = list(emissions.keys())
        emissions_keys.sort(key=key_func)

        emissions_ret = []
        for i, ekey in enumerate(emissions_keys):
            emission = emissions[ekey]
            new_emission = EmissionsTreeModelEmission(emission, i)
            emissions_ret.append(new_emission)

        self.fetch_done.emit(parent, emissions_ret)

    def fetch_seasons(self, parent):
        emission = parent.internalPointer()
        seasons_list = []
        seasons_dict = {}

        logging.debug('Fetching seasons/episodes')

        try:
            episodes = self.client.get_emission_episodes(emission.bo)
        except Exception as e:
            self.fetch_error.emit(parent, e)
            return

        # Sort
        def key_func(ekey):
            return int(episodes[ekey].get_episode_number())
        episodes_keys = list(episodes.keys())
        episodes_keys.sort(key=key_func)

        for key in episodes_keys:
            ep = episodes[key]
            if ep.get_season_number() not in seasons_dict:
                seasons_dict[ep.get_season_number()] = []
            seasons_dict[ep.get_season_number()].append(ep)

        for i, season_number in enumerate(seasons_dict):
            episodes = seasons_dict[season_number]
            new_season = EmissionsTreeModelSeason(season_number, i)
            new_season.emission = emission
            for (j, ep) in enumerate(episodes):
                new_episode = EmissionsTreeModelEpisode(ep, j)
                new_episode.season = new_season
                new_season.episodes.append(new_episode)
            seasons_list.append(new_season)

        self.fetch_done.emit(parent, seasons_list)
