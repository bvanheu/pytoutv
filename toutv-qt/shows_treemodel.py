from PyQt4 import Qt
from PyQt4 import QtCore

import datetime
import sys
import traceback

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

	def get_season(self, number):
		return self.seasons[number]

class FakeSeason:
	def __init__(self, number):
		self.number = number
		self.episodes = {}

	def add_episode(self, episode):
		assert(episode.number not in self.episodes)

		self.episodes[episode.number] = episode
		episode.season = self

	def get_episodes(self):
		return sorted(self.episodes.values(), key = return_number)

	def get_episode(self, number):
		return self.episodes[number]

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
		return sorted(self.shows.values(), key = return_name)


class ShowsTreeModel(Qt.QAbstractItemModel):
	def __init__(self, datasource):
		super(ShowsTreeModel, self).__init__()
		self.datasource = datasource

	def index(self, row, column, parent = Qt.QModelIndex()):
		#print("Index for row %d of parent %s" % (row, str(parent.internalPointer())))
		if not parent.isValid():
			# Create an index for a show
			shows = self.datasource.get_shows()
			show = shows[row]

			assert(show is not None)
			return self.createIndex(row, column, show)

		elif type(parent.internalPointer()) == FakeShow:
			# Create an index for a season
			show = parent.internalPointer()
			seasons = show.get_seasons()
			season = seasons[row]

			return self.createIndex(row, column, season)

		elif type(parent.internalPointer()) == FakeSeason:
			# Create an index for an episode
			season = parent.internalPointer()
			episodes = season.get_episodes()
			episode = episodes[row]

			return self.createIndex(row, column, episode)

		return Qt.QModelIndex()

	def parent(self, child):
		#print("Ask for parent of %s" % str(child.internalPointer()))

		if type(child.internalPointer()) == FakeShow:
			# Show has no parent
			return Qt.QModelIndex()

		elif type(child.internalPointer()) == FakeSeason:
			season = child.internalPointer()
			seasons = season.show.get_seasons()
			row = seasons.index(season)

			return self.createIndex(row, 0, season.show)

		elif type(child.internalPointer()) == FakeEpisode:
			episode = child.internalPointer()
			episodes = episode.season.get_episodes()
			row = episodes.index(episode)

			return self.createIndex(row, 0, episode.season)

		return Qt.QModelIndex()

	def rowCount(self, parent = Qt.QModelIndex()):
		if not parent.isValid():
			# Nombre de shows
			#print(len(self.datasource.get_shows()))
			return len(self.datasource.get_shows())
		elif type(parent.internalPointer()) == FakeShow:
			# Nombre de saisons pour un show
			show = parent.internalPointer()
			return len(show.get_seasons())
		elif type(parent.internalPointer()) == FakeSeason:
			# Nombre d'episodes pour une saison
			season = parent.internalPointer()
			return len(season.get_episodes())

		return 0

	def columnCount(self, parent = Qt.QModelIndex()):
		return 3

	def data_show(self, column, show):
		if column == 0:
			return show.name
		elif column == 1:
			return ""
		elif column == 2:
			return ""

		return "?"


	def data_season(self, column, season):
		if column == 0:
			return "Saison %d" % (season.number)
		elif column == 1:
			return ""
		elif column == 2:
			return ""

		return "?"


	def data_episode(self, column, episode):
		if column == 0:
			return "Episode %d" % (episode.number)
		elif column == 1:
			return "%s" % (episode.name)
		elif column == 2:
			return ""

		return "?"

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if not index.isValid():
			return None

		if role == QtCore.Qt.DisplayRole:
			data_types = {
				FakeShow: self.data_show,
				FakeSeason: self.data_season,
				FakeEpisode: self.data_episode,
			}

			return data_types[type(index.internalPointer())](index.column(), index.internalPointer())

		return None
if __name__ == "__main__":
	data = FakeDataSource("fakedata.xml")
	model = ShowsTreeModel(data)

	for a_show in data.get_shows():
		print(a_show)
		for season in a_show.get_seasons():
			for episode in a_show.get_episodes(season):
				print(episode)

