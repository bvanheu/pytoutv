import datetime
from collections import OrderedDict
from PyQt4 import Qt
from PyQt4 import QtCore


class _DownloadStat:

    def __init__(self):
        self.done_bytes = 0
        self.dt = datetime.datetime.now()


class _DownloadItem:

    def __init__(self, work):
        self._work = work
        self._dl_progress = None
        self._total_segments = None
        self._filename = None
        self._added_dt = datetime.datetime.now()
        self._started_dt = None
        self._done_elapsed = None
        self._last_dl_stat = _DownloadStat()
        self._avg_speed = 0

        # TODO: replace those variable by a single state variable
        self._is_done = False
        self._is_started = False

    def is_started(self):
        return self._is_started

    def set_started(self, is_started):
        self._is_started = is_started
        self._started_dt = datetime.datetime.now()

    def is_done(self):
        return self._is_done

    def set_done(self, is_done):
        self._done_elapsed = self.get_elapsed()
        self._avg_speed = 0
        self._is_done = is_done

    def get_dl_progress(self):
        return self._dl_progress

    def get_avg_download_speed(self):
        return self._avg_speed

    def _compute_avg_speed(self):
        done_bytes = self.get_dl_progress().get_done_bytes()
        now = datetime.datetime.now()

        if self.get_elapsed().seconds >= 3:
            time_delta = now - self._last_dl_stat.dt
            time_delta = time_delta.total_seconds()
            bytes_delta = done_bytes - self._last_dl_stat.done_bytes
            self._avg_speed = bytes_delta / time_delta

        self._last_dl_stat.done_bytes = done_bytes
        self._last_dl_stat.dt = datetime.datetime.now()

    def set_dl_progress(self, dl_progress):
        self._dl_progress = dl_progress

        if not self.is_done() and self.is_started():
            self._compute_avg_speed()

    def get_work(self):
        return self._work

    def set_work(self, work):
        self._work = work

    def get_total_segments(self):
        return self._total_segments

    def set_total_segments(self, total_segments):
        self._total_segments = total_segments

    def get_filename(self):
        return self._filename

    def set_filename(self, filename):
        self._filename = filename

    def get_progress_percent(self):
        if not self._is_started or self.get_dl_progress() is None:
            return 0
        if self._is_done:
            return 100

        num = self.get_dl_progress().get_done_segments()
        denom = self.get_total_segments()

        return round(num / denom * 100)

    def get_added_dt(self):
        return self._added_dt

    def get_started_dt(self):
        return self._started_dt

    def get_elapsed(self):
        if not self.is_started():
            return datetime.timedelta()
        if self.is_done():
            return self._done_elapsed

        return datetime.datetime.now() - self.get_started_dt()


class QDownloadsTableModel(Qt.QAbstractTableModel):
    _HEADER = [
        'Emission',
        'Season/ep.',
        'Episode',
        'Filename',
        'Sections',
        'Downloaded',
        'Added',
        'Elapsed',
        'Speed',
        'Progress',
        'Status',
    ]

    def __init__(self, download_manager, parent=None):
        super().__init__(parent)

        self._download_manager = download_manager
        self._download_list = OrderedDict()

        self._setup_signals()

    def get_progress_col(self):
        return 9

    def get_download_item_at_row(self, row):
        episode_id = list(self._download_list.keys())[row]

        return self._download_list[episode_id]

    def download_item_exists(self, episode):
        return episode.get_id() in self._download_list

    def _setup_signals(self):
        dl_manager = self._download_manager

        dl_manager.download_created.connect(self._on_download_created)
        dl_manager.download_started.connect(self._on_download_started)
        dl_manager.download_progress.connect(self._on_download_progress)
        dl_manager.download_finished.connect(self._on_download_finished)

    def _on_download_created(self, work):
        episode_id = work.get_episode().get_id()

        if episode_id in self._download_list:
            print('I DON\'T KNOW WHAT TO DO!!!')
            return

        new_position = len(self._download_list)
        self.beginInsertRows(Qt.QModelIndex(), new_position, new_position)
        self._download_list[episode_id] = _DownloadItem(work)
        self.endInsertRows()

    def _get_download_item(self, episode):
        return self._download_list[episode.get_id()]

    def _on_download_started(self, work, dl_progress, filename,
                             total_segments):
        episode = work.get_episode()
        item = self._get_download_item(episode)

        item.set_dl_progress(dl_progress)
        item.set_total_segments(total_segments)
        item.set_filename(filename)
        item.set_started(True)

        self._signal_episode_data_changed(episode)

    def _on_download_progress(self, work, dl_progress):
        episode = work.get_episode()
        item = self._get_download_item(episode)

        item.set_dl_progress(dl_progress)

        self._signal_episode_data_changed(episode)

    def _on_download_finished(self, work):
        episode = work.get_episode()
        item = self._get_download_item(episode)

        item.set_done(True)

        self._signal_episode_data_changed(episode)

    def _signal_episode_data_changed(self, episode):
        episode_id = episode.get_id()
        index_start = self.index_from_id(episode_id, 0)
        index_end = self.index_from_id(episode_id, len(self._HEADER) - 1)

        self.dataChanged.emit(index_start, index_end)

    def exit(self):
        self._download_manager.exit()

    def index(self, row, column, parent):
        key = list(self._download_list.keys())[row]
        dl_item = self._download_list[key]
        work = dl_item.get_work()
        episode_id = work.get_episode().get_id()
        idx = self.createIndex(row, column, None)

        return idx

    def parent(self, child):
        return Qt.QModelIndex()

    def index_from_id(self, episode_id, column):
        row = list(self._download_list.keys()).index(episode_id)

        return self.createIndex(row, column, None)

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
            dl_item = self._download_list[episode_id]
            dl_progress = dl_item.get_dl_progress()

            work = dl_item.get_work()
            episode = work.get_episode()

            if col == 0:
                # Emission
                return episode.get_emission().get_title()
            elif col == 1:
                # Season/episode
                return episode.get_sae()
            elif col == 2:
                # Episode
                return episode.get_title()
            elif col == 3:
                # Filename
                filename = dl_item.get_filename()
                if filename is None:
                    filename = '?'

                return filename
            elif col == 4:
                # Segments
                done_segments = 0
                if dl_progress is not None:
                    done_segments = dl_progress.get_done_segments()
                total_segments = dl_item.get_total_segments()
                if total_segments is None:
                    total_segments = '?'

                return '{}/{}'.format(done_segments, total_segments)
            elif col == 5:
                # Bytes
                if dl_progress is None:
                    return 0

                done_bytes = dl_progress.get_done_bytes()
                if done_bytes < (1 << 10):
                    dl = '{} B'.format(done_bytes)
                elif done_bytes < (1 << 20):
                    dl = '{:.1f} kiB'.format(done_bytes / (1 << 10))
                elif done_bytes < (1 << 30):
                    dl = '{:.1f} MiB'.format(done_bytes / (1 << 20))
                else:
                    dl = '{:.1f} GiB'.format(done_bytes / (1 << 30))

                return dl
            elif col == 6:
                # Added date
                return dl_item.get_added_dt().strftime('%Y-%m-%d %H:%M:%S')
            elif col == 7:
                # Elapsed time
                total_seconds = dl_item.get_elapsed().seconds
                minutes = total_seconds // 60
                seconds = total_seconds - (minutes * 60)

                return '{}:{:02}'.format(minutes, seconds)
            elif col == 8:
                # Average download speed
                return '{:.2f} kB/s'.format(dl_item.get_avg_download_speed() / 1024)
            elif col == 9:
                # Progress bar
                return None
            elif col == 10:
                # Status
                if dl_item.is_done():
                    return 'Done'
                if dl_item.is_started():
                    return 'Started'

                return 'Queued'

    def headerData(self, col, ori, role):
        if ori == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return QDownloadsTableModel._HEADER[col]

        return None
