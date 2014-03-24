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


class FakeShow:
    def __init__(self, name):
        self.name = name
        self.seasons = {}

    def __repr__(self):
        return "Show %s" % (self.name)

    def add_episode(self, season_number, episode):
        if season_number not in self.seasons:
            season = FakeSeason(season_number)
            season.show = self
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

        self.shows = {}

        for node in root:
            if node.tag == "Episode":
                series_id = int(node.find("seriesid").text)
                episode_name = str(node.find("EpisodeName").text)
                number = int(node.find("EpisodeNumber").text)
                season_number = int(node.find("SeasonNumber").text)

                show = self.shows[series_id]

                show.add_episode(season_number, FakeEpisode(episode_name, number))

            elif node.tag == "Series":
                series_id = int(node.find("id").text)
                series_name = str(node.find("SeriesName").text)
                self.shows[series_id] = FakeShow(series_name)
    # Returns a list of FakeShow in alphabetical order
    def get_shows(self):
        time.sleep(2)
        return sorted(self.shows.values(), key = return_name)

    def get_season_for(self, show_name):
        time.sleep(2)
        for show in self.shows.values():
            if show.name != show_name:
                continue

            return show.seasons.values()
        print("Not found %s", show_name)
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


class ShowsTreeModelShow:
    def __init__(self, name):
        self.name = name
        self.seasons = []
        self.loading_item = LoadingItem(self)

        # Have we fetched this show's seasons?
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


class ShowsTreeModelSeason:
    def __init__(self, number):
        self.number = number
        self.episodes = []
        self.loading_item = LoadingItem(self)

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


class ShowsTreeModelEpisode:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.loading_item = LoadingItem(self)

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


class ShowsTreeModel(Qt.QAbstractItemModel):
    def __init__(self, datasource):
        super(ShowsTreeModel, self).__init__()
        self.shows = []
        self.datasource = datasource
        self.loading_item = LoadingItem(None)
        self.fetch_thread = ShowsTreeModelFetchThread(self.datasource)

        # Have we fetched the shows ?
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
            # Create an index for a show
            if self.fetched == FetchState.Done:
                show = self.shows[row]
                return self.createIndex(row, column, show)
            else:
                return self.createIndex(row, column, self.loading_item)

        elif type(parent.internalPointer()) == ShowsTreeModelShow:
            # Create an index for a season
            show = parent.internalPointer()
            if show.fetched == FetchState.Done:
                season = show.seasons[row]
                return self.createIndex(row, column, season)
            else:
                return self.createIndex(row, column, show.loading_item)

        elif type(parent.internalPointer()) == ShowsTreeModelSeason:
            # Create an index for an episode
            season = parent.internalPointer()
            if season.fetched == FetchState.Done:
                episode = season.episodes[row]
                return self.createIndex(row, column, episode)
            else:
                return self.createIndex(row, column, season.loading_item)

        return Qt.QModelIndex()

    def parent(self, child):
        if type(child.internalPointer()) == ShowsTreeModelShow:
            # Show has no parent
            return Qt.QModelIndex()

        elif type(child.internalPointer()) == ShowsTreeModelSeason:
            season = child.internalPointer()
            row = season.show.seasons.index(season)

            return self.createIndex(row, 0, season.show)

        elif type(child.internalPointer()) == ShowsTreeModelEpisode:
            episode = child.internalPointer()
            row = episode.season.episodes.index(episode)

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
        # TODO: Maybe add a rowCount method in the ShowsTreeModel* classes and just call it.
        if not parent.isValid():
            # Nombre de shows
            if self.fetched == FetchState.Done:
                return len(self.shows)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == ShowsTreeModelShow:
            # Nombre de saisons pour un show
            show = parent.internalPointer()
            if show.fetched == FetchState.Done:
                return len(show.seasons)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == ShowsTreeModelSeason:
            # Nombre d'episodes pour une saison
            season = parent.internalPointer()
            if season.fetched == FetchState.Done:
                return len(season.episodes)
            else:
                # The "Loading" item
                return 1

        elif type(parent.internalPointer()) == ShowsTreeModelEpisode:
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
        self.beginInsertRows(parent, 0, len(children_list) - 1)

        if parent.isValid():
            parent.internalPointer().set_children(children_list)
            parent.internalPointer().fetched = FetchState.Done
        else:
            self.shows = children_list
            self.fetched = FetchState.Done
        self.endInsertRows()
        pass

    def fetchInit(self, parent):
        if parent.isValid():
            parent.internalPointer().fetched = FetchState.Started
            self.new_data_required.emit(parent)
        else:
            self.fetched = FetchState.Started
            self.new_data_required.emit(parent)



    def itemExpanded(self, parent):
        if parent.internalPointer().fetched == FetchState.Nope:
            self.fetchInit(parent)

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        return index.internalPointer().data(index, role)


class ShowsTreeModelFetchThread(Qt.QThread):
    def __init__(self, datasource):
        super(ShowsTreeModelFetchThread, self).__init__()
        self.queue = queue.Queue()
        self.datasource = datasource

    work_done = QtCore.pyqtSignal(object, list)

    def new_work_piece(self, parent):
        print("New work piece for %s" % parent.internalPointer())
        self.queue.put(parent)

    def fetch_shows(self, parent):
        shows = self.datasource.get_shows()
        shows_ret = []
        for show in shows:
            shows_ret.append(ShowsTreeModelShow(show.name))
        self.work_done.emit(parent, shows_ret)

    def fetch_seasons(self, parent):
        show = parent.internalPointer()
        seasons = self.datasource.get_season_for(show.name)
        seasons_ret = []
        print("A")
        for s in seasons:
            seasons_ret.append(ShowsTreeModelSeason(s.number))
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
                self.fetch_shows(parent)
            elif type(parent.internalPointer()) == ShowsTreeModelShow:
                print("C")
                self.fetch_seasons(parent)
                print("D")
            elif type(parent.internalPointer()) == ShowsTreeModelSeason:
                self.fetch_episodes(parent)


if __name__ == "__main__":
    data = FakeDataSource("fakedata.xml")
    model = ShowsTreeModel(data)

    for a_show in data.get_shows():
        print(a_show)
        for season in a_show.get_seasons():
            for episode in a_show.get_episodes(season):
                print(episode)
