from PyQt4 import Qt
from PyQt4 import QtCore

from collections import OrderedDict


class Internal:

    def __init__(self, episode_id):
        self._episode_id = episode_id

    def get_episode_id(self):
        return self._episode_id


class QDownloadsTableModel(Qt.QAbstractTableModel):
    _HEADER = [
        'Emission',
        'Season',
        'Episode',
        'Filename',
        'Sections',
        'Bytes',
        'Progress',
        '%',
    ]

    def __init__(self, download_manager, parent=None):
        super().__init__(parent)
        self._download_manager = download_manager

        self._download_list = OrderedDict()

        self._setup_signals()

    def get_progress_col(self):
        return 6

    def _setup_signals(self):
        self._download_manager.download_created.connect(
            self._on_download_created)
        self._download_manager.download_started.connect(
            self._on_download_started)
        self._download_manager.download_progress.connect(
            self._on_download_progress)
        self._download_manager.download_finished.connect(
            self._on_download_finished)

    def _on_download_created(self, work):
        episode_id = work.get_episode().Id

        if episode_id in self._download_list:
            print('I DON\'T KNOW WHAT TO DO!!!')
            return

        new_position = len(self._download_list)
        self.beginInsertRows(Qt.QModelIndex(), new_position, new_position)
        self._download_list[episode_id] = (work, None)
        self.endInsertRows()

    def _on_download_started(self, work, progress):
        episode_id = work.get_episode().Id
        self._download_list[episode_id] = (work, progress)
        self._signal_episode_data_changed(episode_id)

    def _on_download_progress(self, work, progress):
        episode_id = work.get_episode().Id
        self._download_list[episode_id] = (work, progress)
        self._signal_episode_data_changed(episode_id)

    def _on_download_finished(self, work):
        episode_id = work.get_episode().Id
        self._download_list[episode_id] = (work, 'tourlou')
        self._signal_episode_data_changed(episode_id)

    def _signal_episode_data_changed(self, episode_id):
        index_start = self.index_from_id(episode_id, 0)
        index_end = self.index_from_id(episode_id, len(self._HEADER) - 1)
        self.dataChanged.emit(index_start, index_end)

    def exit(self):
        self._download_manager.exit()

    def index(self, row, column, parent):
        key = list(self._download_list.keys())[row]
        (work, progress) = self._download_list[key]
        idx = self.createIndex(row, column, Internal(work.get_episode().Id))
        return idx

    def parent(self, child):
        return Qt.QModelIndex()

    def index_from_id(self, episode_id, column):
        row = list(self._download_list.keys()).index(episode_id)
        return self.createIndex(row, column, Internal(episode_id))

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._download_list)
        else:
            return 0

    def columnCount(self, parent):
        return len(QDownloadsTableModel._HEADER)

    def data(self, index, role):
        col = index.column()
        if role == QtCore.Qt.DisplayRole:

            # I don't know why, calling index.internalPointer() seems to
            # segfault
            row = index.row()
            episode_id = list(self._download_list.keys())[row]
            (work, progress) = self._download_list[episode_id]
            episode = work.get_episode()

            if col == 0:
                'Emission'
                return episode.Title
            elif col == 1:
                'Season'
                return 'bleh'
            elif col == 2:
                'Episode'
                return 'bleh'
            elif col == 3:
                'Filename'
                return 'bleh'
            elif col == 4:
                'Sections'
                if progress is None:
                    return 'not started'
                elif progress == "tourlou":
                    return 'finished'
                else:
                    return '{}/{}'.format(progress.get_done_segments_count(),
                                          progress.get_total_segments_count())
            elif col == 5:
                if progress == "tourlou":
                    return "FENI"
                elif progress is None:
                    return "PAS PARTI"
                else:
                    return '{}'.format(progress.get_done_bytes_count())
            elif col == 6:
                'Progress'
                return 'bleh'
            elif col == 7:
                '%'
                return 'bleh'

    def headerData(self, col, ori, role):
        if ori == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return QDownloadsTableModel._HEADER[col]

        return None

    def get_download_at_row(self, row):
        episode_id = list(self._download_list.keys())[row]
        return self._download_list[episode_id]
