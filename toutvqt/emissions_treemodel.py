from PyQt4 import Qt
from PyQt4 import QtCore
import datetime
import sys
import traceback
import time
import queue
import xml.etree.ElementTree as ET


def return_name(x):
    return x.name


def return_number(x):
    return x.number


class FakeEmission:
    def __init__(self, name):
        self.name = name
        self.seasons = {}

    def __repr__(self):
        return "Emission %s" % (self.name)

    def add_episode(self, season_number, episode):
        if season_number not in self.seasons:
            season = FakeSeason(season_number)
            season.emission = self
            self.seasons[season_number] = season

        self.seasons[season_number].add_episode(episode)

    def get_seasons(self):
        return sorted(self.seasons.values(), key = return_number)


#    def get_season(self, number):
#        return self.seasons[number]
class FakeSeason:
    def __init__(self, number):
        self.number = number
        self.episodes = {}

    def add_episode(self, episode):
        assert(episode.number not in self.episodes)

        self.episodes[episode.number] = episode
        episode.season = self

    def get_episodes(self):
        time.sleep(2)
        return sorted(self.episodes.values(), key = return_number)


#    def get_episode(self, number):
#        return self.episodes[number]
class FakeEpisode:
    def __init__(self, name, number):
        self.name = name
        self.duration = datetime.timedelta(minutes = 22, seconds = 34)
        self.number = number

    def __repr__(self):
        return "Episode S%02dE%02d %s" % (self.season.number, self.number, self.name)


class FakeDataSource:
    def __init__(self, xmlFile):
        tree = ET.parse(xmlFile)
        root = tree.getroot()

        self.emissions = {}

        for node in root:
            if node.tag == "Episode":
                series_id = int(node.find("seriesid").text)
                episode_name = str(node.find("EpisodeName").text)
                number = int(node.find("EpisodeNumber").text)
                season_number = int(node.find("SeasonNumber").text)

                emission = self.emissions[series_id]

                emission.add_episode(season_number, FakeEpisode(episode_name, number))

            elif node.tag == "Series":
                series_id = int(node.find("id").text)
                series_name = str(node.find("SeriesName").text)
                self.emissions[series_id] = FakeEmission(series_name)
    # Returns a list of FakeEmission in alphabetical order
    def get_emissions(self):
        time.sleep(2)
        return sorted(self.emissions.values(), key = return_name)

    def get_season_for(self, emission_name):
        time.sleep(2)
        for emission in self.emissions.values():
            if emission.name != emission_name:
                continue

            return emission.seasons.values()
        print("Not found %s", emission_name)
        assert(False)


class FetchState:
    Nope = 0
    Started = 1
    Done = 2


class LoadingItem:
    def __init__(self, parent):
        self.parent = parent

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "Loading..."
            else:
                return ""


class EmissionsTreeModelEmission:
    def __init__(self, name, row_in_parent):
        self.name = name
        self.seasons = []
        self.loading_item = LoadingItem(self)
        self.row_in_parent = row_in_parent

        # Have we fetched this emission's seasons?
        self.fetched = FetchState.Nope

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self.name
            elif column == 1:
                return ""
            elif column == 2:
                return ""

            return "?"

    def set_children(self, c):
        self.seasons = c


class EmissionsTreeModelSeason:
    def __init__(self, number, row_in_parent):
        self.number = number
        self.episodes = []
        self.loading_item = LoadingItem(self)
        self.row_in_parent = row_in_parent

        # Have we fetched this season's episodes?
        self.fetched = FetchState.Nope

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "Saison %d" % (self.number)
            elif column == 1:
                return ""
            elif column == 2:
                return ""

            return "?"
    def set_children(self, c):
        self.episodes = c


class EmissionsTreeModelEpisode:
    def __init__(self, name, number, row_in_parent):
        self.name = name
        self.number = number
        self.loading_item = LoadingItem(self)
        self.row_in_parent = row_in_parent

    def data(self, index, role):
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "Episode %d" % (self.number)
            elif column == 1:
                return "%s" % (self.name)
            elif column == 2:
                return ""

            return "?"


class EmissionsTreeModel(Qt.QAbstractItemModel):
    def __init__(self, datasource):
        super(EmissionsTreeModel, self).__init__()
        self.emissions = []
        self.datasource = datasource
        self.loading_item = LoadingItem(None)
        self.fetch_thread = EmissionsTreeModelFetchThread(self.datasource)

        # Have we fetched the emissions ?
        self.fetched = FetchState.Nope

        # Connect signals between us and the thread
        self.new_data_required.connect(self.fetch_thread.new_work_piece)
        self.fetch_thread.work_done.connect(self.fetchDone)

        self.fetch_thread.start()

        # Fetch the root elements
        self.fetchInit(Qt.QModelIndex())

    new_data_required = QtCore.pyqtSignal(object)

    def index(self, row, column, parent = Qt.QModelIndex()):
        """Returns a QModelIndex to represent a cell of a child of parent."""
        #print("Index of %s %s r=%d c=%d" % (parent.internalPointer(), parent.isValid(), row, column))
        if not parent.isValid():
            # Create an index for a emission
            if self.fetched == FetchState.Done:
                emission = self.emissions[row]
                return self.createIndex(row, column, emission)
            else:
                return self.createIndex(row, column, self.loading_item)

        elif type(parent.internalPointer()) == EmissionsTreeModelEmission:
            # Create an index for a season
            emission = parent.internalPointer()
            if emission.fetched == FetchState.Done:
                season = emission.seasons[row]
                return self.createIndex(row, column, season)
            else:
                return self.createIndex(row, column, emission.loading_item)

        elif type(parent.internalPointer()) == EmissionsTreeModelSeason:
            # Create an index for an episode
            season = parent.internalPointer()
            if season.fetched == FetchState.Done:
                episode = season.episodes[row]
                return self.createIndex(row, column, episode)
            else:
                return self.createIndex(row, column, season.loading_item)

        return Qt.QModelIndex()

    def parent(self, child):
        if type(child.internalPointer()) == EmissionsTreeModelEmission:
            # Emission has no parent
            return Qt.QModelIndex()

        elif type(child.internalPointer()) == EmissionsTreeModelSeason:
            emission = child.internalPointer().emission
            row = emission.row_in_parent

            return self.createIndex(row, 0, emission)

        elif type(child.internalPointer()) == EmissionsTreeModelEpisode:
            season = child.internalPointer().season
            row = season.row_in_parent

            return self.createIndex(row, 0, episode.season)

        elif type(child.internalPointer()) == LoadingItem:
            loading_item = child.internalPointer()
            if loading_item.parent is not None:
                return self.createIndex(0, 0, loading_item.parent)
            else:
                return Qt.QModelIndex()

        return Qt.QModelIndex()

    def rowCount(self, parent = Qt.QModelIndex()):
        #print("RowCount of %s %s" % (str(parent.internalPointer()), parent.isValid()))
        # TODO: Maybe add a rowCount method in the EmissionsTreeModel* classes and just call it.
        if not parent.isValid():
            # Nombre de emissions
            if self.fetched == FetchState.Done:
                return len(self.emissions)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == EmissionsTreeModelEmission:
            # Nombre de saisons pour un emission
            emission = parent.internalPointer()
            if emission.fetched == FetchState.Done:
                return len(emission.seasons)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == EmissionsTreeModelSeason:
            # Nombre d'episodes pour une saison
            season = parent.internalPointer()
            if season.fetched == FetchState.Done:
                return len(season.episodes)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == EmissionsTreeModelEpisode:
            return 0

        elif type(parent.internalPointer()) == LoadingItem:
            return 0


        print("Damn")
        # All possible types should be covered in the if/elif
        assert(False)

    def columnCount(self, parent = Qt.QModelIndex()):
        return 3

    def fetchDone(self, parent, children_list):
        """A fetch work is complete."""
        print("fetchDone for %s" % (parent.internalPointer()))

        self.beginRemoveRows(parent, 0, 0)
        if parent.isValid():
            parent.internalPointer().fetched = FetchState.Done
        else:
            self.fetched =  FetchState.Done
        self.endRemoveRows()

        self.beginInsertRows(parent, 0, len(children_list) - 1)
        if parent.isValid():
            parent.internalPointer().set_children(children_list)
        else:
            self.emissions = children_list
        self.endInsertRows()


    def fetchInit(self, parent):
        if parent.isValid():
            parent.internalPointer().fetched = FetchState.Started
        else:
            self.fetched = FetchState.Started

        parent = Qt.QModelIndex(parent)
        self.new_data_required.emit(parent)

    def itemExpanded(self, parent):
        if parent.internalPointer().fetched == FetchState.Nope:
            self.fetchInit(parent)

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        return index.internalPointer().data(index, role)


class EmissionsTreeModelFetchThread(Qt.QThread):
    def __init__(self, datasource):
        super(EmissionsTreeModelFetchThread, self).__init__()
        self.queue = queue.Queue()
        self.datasource = datasource

    work_done = QtCore.pyqtSignal(object, list)

    def new_work_piece(self, parent):
        print("New work piece for %s" % parent.internalPointer())
        self.queue.put(parent)

    def fetch_emissions(self, parent):
        emissions = self.datasource.get_emissions()
        emissions_ret = []
        for (i, emission) in enumerate(emissions):
            new_emission = EmissionsTreeModelEmission(emission.name, i)
            emissions_ret.append(new_emission)
        self.work_done.emit(parent, emissions_ret)

    def fetch_seasons(self, parent):
        emission = parent.internalPointer()
        seasons = self.datasource.get_season_for(emission.name)
        seasons_ret = []
        print("A")
        for (i, s) in enumerate(seasons):
            new_season = EmissionsTreeModelSeason(s.number, i)
            new_season.emission = emission
            seasons_ret.append(new_season)
        print("B")
        self.work_done.emit(parent, seasons_ret)

    def fetch_episodes(self, parent):
        print("Ohlala")
        assert(False)

    def run(self):
        while True:
            parent = self.queue.get()
            print("Processing work piece for %s" % parent.internalPointer())
            if not parent.isValid():
                self.fetch_emissions(parent)
            elif type(parent.internalPointer()) == EmissionsTreeModelEmission:
                print("C")
                self.fetch_seasons(parent)
                print("D")
            elif type(parent.internalPointer()) == EmissionsTreeModelSeason:
                self.fetch_episodes(parent)


if __name__ == "__main__":
    data = FakeDataSource("fakedata.xml")
    model = EmissionsTreeModel(data)

    for a_emission in data.get_emissions():
        print(a_emission)
        for season in a_emission.get_seasons():
            for episode in a_emission.get_episodes(season):
                print(episode)
