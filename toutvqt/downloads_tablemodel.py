import logging
import datetime
from collections import OrderedDict
from PyQt4 import Qt
from PyQt4 import QtCore


class _DownloadStat:
    def __init__(self):
        self.done_bytes = 0
        self.dt = None


class DownloadItemState:
    QUEUED = 0
    RUNNING = 1
    PAUSED = 2
    CANCELLED = 3
    ERROR = 4
    DONE = 5


class _DownloadItem:
    def __init__(self, work):
        self._work = work
        self._dl_progress = None
        self._total_segments = None
        self._filename = None
        self._added_dt = datetime.datetime.now()
        self._started_dt = None
        self._end_elapsed = None
        self._last_dl_stat = None
        self._avg_speed = 0
        self._error = None
        self._state = DownloadItemState.QUEUED

    def set_error(self, ex):
        self._error = ex

    def get_error(self):
        return self._error

    def get_state(self):
        return self._state

    def set_state(self, state):
        if state == DownloadItemState.RUNNING:
            self._started_dt = datetime.datetime.now()
        elif state in [
            DownloadItemState.DONE,
            DownloadItemState.CANCELLED,
            DownloadItemState.ERROR
        ]:
            self._end_elapsed = self.get_elapsed()
            self._avg_speed = 0

        self._state = state

    def get_dl_progress(self):
        return self._dl_progress

    def get_avg_download_speed(self):
        return self._avg_speed

    def _compute_avg_speed(self, dt):
        done_bytes = self.get_dl_progress().get_done_bytes()
        now = dt

        if self._last_dl_stat is None:
            self._last_dl_stat = _DownloadStat()
            self._last_dl_stat.done_bytes = done_bytes
            self._last_dl_stat.dt = now
            return

        time_delta = now - self._last_dl_stat.dt
        time_delta = time_delta.total_seconds()
        bytes_delta = done_bytes - self._last_dl_stat.done_bytes
        last_speed = bytes_delta / time_delta
        self._avg_speed = 0.2 * last_speed + 0.8 * self._avg_speed

        self._last_dl_stat.done_bytes = done_bytes
        self._last_dl_stat.dt = now

    def set_dl_progress(self, dl_progress, dt):
        self._dl_progress = dl_progress

        if self.get_state() == DownloadItemState.RUNNING:
            self._compute_avg_speed(dt)

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
        is_init = (self.get_state() == DownloadItemState.QUEUED)
        if is_init or self.get_dl_progress() is None:
            return 0
        if self.get_state() == DownloadItemState.DONE:
            return 100

        num = self.get_dl_progress().get_done_segments()
        denom = self.get_total_segments()

        return round(num / denom * 100)

    def get_added_dt(self):
        return self._added_dt

    def get_started_dt(self):
        return self._started_dt

    def get_elapsed(self):
        if self.get_state() == DownloadItemState.QUEUED:
            return datetime.timedelta()
        elif self._end_elapsed is not None:
            return self._end_elapsed

        return datetime.datetime.now() - self.get_started_dt()

    def get_estimated_size(self):
        if self.get_state() == DownloadItemState.DONE:
            return self.get_dl_progress().get_done_bytes()

        if self.get_dl_progress() is None:
            return None

        done_segments_bytes = self.get_dl_progress().get_done_segments_bytes()
        done_segments = self.get_dl_progress().get_done_segments()
        total_segments = self.get_total_segments()

        if done_segments == 0 or done_segments_bytes == 0:
            return None

        estimated_size = total_segments / done_segments * done_segments_bytes

        return estimated_size


class QDownloadsTableModel(Qt.QAbstractTableModel):
    _HEADER = [
        'Emission',
        'Season/ep.',
        'Episode',
        'Filename',
        'Sections',
        'Downloaded',
        'Estimated size',
        'Added',
        'Elapsed',
        'Speed',
        'Progress',
        'Status',
        'Quality',
    ]
    _status_msg_handlers = {
        DownloadItemState.QUEUED: lambda i: 'Queued',
        DownloadItemState.RUNNING: lambda i: 'Running',
        DownloadItemState.PAUSED: lambda i: 'Paused',
        DownloadItemState.CANCELLED: lambda i: 'Cancelled',
        DownloadItemState.ERROR: lambda i: 'Error: {}'.format(i.get_error()),
        DownloadItemState.DONE: lambda i: 'Done'
    }
    download_finished = QtCore.pyqtSignal(object)
    download_cancelled = QtCore.pyqtSignal(object)

    def __init__(self, download_manager, parent=None):
        super().__init__(parent)

        self._download_manager = download_manager
        self._download_list = OrderedDict()

        self._delayed_update_calls = []

        self._setup_signals()
        self._setup_timer()

    def get_progress_col(self):
        return 10

    def get_download_item_at_row(self, row):
        return list(self._download_list.values())[row]

    def download_item_exists(self, episode_id, quality):
        key = (episode_id, quality)
        return key in self._download_list

    def cancel_download_at_row(self, row):
        # Get download item
        dl_item = self.get_download_item_at_row(row)

        # Ask download manager to cancel its work
        self._download_manager.cancel_work(dl_item.get_work())

    def remove_episode_id_item(self, episode_id, quality):
        key = (episode_id, quality)
        if key not in self._download_list:
            return

        row = list(self._download_list.keys()).index(key)
        self.beginRemoveRows(Qt.QModelIndex(), row, row)
        del self._download_list[key]
        self.endRemoveRows()

    def remove_item_at_row(self, row):
        self.beginRemoveRows(Qt.QModelIndex(), row, row)
        key = list(self._download_list.keys())[row]
        del self._download_list[key]
        self.endRemoveRows()

    def _setup_timer(self):
        self._refresh_timer = Qt.QTimer(self)
        self._refresh_timer.timeout.connect(self._on_timer_timeout)
        self._refresh_timer.setInterval(500)
        self._refresh_timer.start()

    def _setup_signals(self):
        dlman = self._download_manager

        dlman.download_created.connect(self._on_download_created_delayed)
        dlman.download_started.connect(self._on_download_started_delayed)
        dlman.download_progress.connect(self._on_download_progress_delayed)
        dlman.download_finished.connect(self._on_download_finished_delayed)
        dlman.download_error.connect(self._on_download_error_delayed)
        dlman.download_cancelled.connect(self._on_download_cancelled_delayed)

    def _on_download_created_delayed(self, work):
        self._delayed_update_calls.append((self._on_download_created, [work]))

    def _on_download_started_delayed(self, work, dl_progress, filename,
                                     total_segments):
        now = datetime.datetime.now()
        self._delayed_update_calls.append(
            (self._on_download_started, [work, dl_progress, filename,
                                         total_segments, now]))

    def _on_download_progress_delayed(self, work, dl_progress):
        now = datetime.datetime.now()
        self._delayed_update_calls.append((self._on_download_progress,
                                          [work, dl_progress, now]))

    def _on_download_finished_delayed(self, work):
        self._delayed_update_calls.append((self._on_download_finished, [work]))

    def _on_download_error_delayed(self, work, ex):
        self._delayed_update_calls.append((self._on_download_error,
                                           [work, ex]))

    def _on_download_cancelled_delayed(self, work):
        self._delayed_update_calls.append((self._on_download_cancelled,
                                           [work]))

    def _on_download_created(self, work):
        episode_id = work.get_episode().get_id()
        quality = work.quality
        key = (episode_id, quality)

        if key in self._download_list:
            msg = 'Episode {} already in download list'.format(episode_id)
            logging.warning(msg)
            return

        new_position = len(self._download_list)
        self.beginInsertRows(Qt.QModelIndex(), new_position, new_position)
        self._download_list[key] = _DownloadItem(work)
        self.endInsertRows()

    def _get_download_item(self, episode, quality):
        key = (episode.get_id(), quality)
        return self._download_list[key]

    def _on_download_started(self, work, dl_progress, filename,
                             total_segments, now):
        episode = work.get_episode()
        quality = work.quality

        item = self._get_download_item(episode, quality)

        item.set_dl_progress(dl_progress, now)
        item.set_total_segments(total_segments)
        item.set_filename(filename)
        item.set_state(DownloadItemState.RUNNING)

    def _on_download_progress(self, work, dl_progress, now):
        episode = work.get_episode()
        quality = work.quality

        item = self._get_download_item(episode, quality)

        item.set_dl_progress(dl_progress, now)

    def _on_download_finished(self, work):
        episode = work.get_episode()
        quality = work.quality

        item = self._get_download_item(episode, quality)

        item.set_state(DownloadItemState.DONE)
        self.download_finished.emit(work)

    def _on_download_error(self, work, ex):
        episode = work.get_episode()
        quality = work.quality

        item = self._get_download_item(episode, quality)

        item.set_state(DownloadItemState.ERROR)
        item.set_error(ex)

    def _on_download_cancelled(self, work):
        episode = work.get_episode()
        quality = work.quality

        item = self._get_download_item(episode, quality)

        item.set_state(DownloadItemState.CANCELLED)
        self.download_cancelled.emit(work)

    def _on_timer_timeout(self):
        for func, args in self._delayed_update_calls:
            func(*args)

        self._delayed_update_calls = []

        self._signal_all_data_changed()

    def _signal_all_data_changed(self):
        index_start = self.createIndex(0, 0, None)
        last_row = len(self._download_list) - 1
        last_col = len(self._HEADER) - 1
        index_end = self.createIndex(last_row, last_col, None)

        self.dataChanged.emit(index_start, index_end)

    def exit(self):
        self._download_manager.exit()

    def index(self, row, column, parent):
        keys = list(self._download_list.keys())
        if row >= len(keys):
            return Qt.QModelIndex()
        key = keys[row]
        dl_item = self._download_list[key]
        work = dl_item.get_work()
        idx = self.createIndex(row, column, work)

        return idx

    def parent(self, child):
        return Qt.QModelIndex()

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._download_list)
        else:
            return 0

    def columnCount(self, parent):
        return len(QDownloadsTableModel._HEADER)

    @staticmethod
    def _format_size(size):
        if size < (1 << 10):
            s = '{} B'.format(size)
        elif size < (1 << 20):
            s = '{:.1f} kiB'.format(size / (1 << 10))
        elif size < (1 << 30):
            s = '{:.1f} MiB'.format(size / (1 << 20))
        else:
            s = '{:.1f} GiB'.format(size / (1 << 30))

        return s

    def data(self, index, role):
        col = index.column()
        if role == QtCore.Qt.DisplayRole:

            # I don't know why, calling index.internalPointer() seems to
            # segfault
            row = index.row()
            key = list(self._download_list.keys())[row]
            dl_item = self._download_list[key]
            dl_progress = dl_item.get_dl_progress()

            work = dl_item.get_work()
            episode = work.get_episode()
            quality = work.quality

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
                # Downloaded bytes
                if dl_progress is None:
                    return 0

                done_bytes = dl_progress.get_done_bytes()
                dl = QDownloadsTableModel._format_size(done_bytes)

                return dl
            elif col == 6:
                # Estimated size
                estimated_size = dl_item.get_estimated_size()
                if estimated_size is None:
                    return '?'

                sz = QDownloadsTableModel._format_size(estimated_size)

                return sz
            elif col == 7:
                # Added date
                return dl_item.get_added_dt().strftime('%Y-%m-%d %H:%M:%S')
            elif col == 8:
                # Elapsed time
                total_seconds = dl_item.get_elapsed().seconds
                minutes = total_seconds // 60
                seconds = total_seconds - (minutes * 60)

                return '{}:{:02}'.format(minutes, seconds)
            elif col == 9:
                # Average download speed
                if dl_item.get_state() != DownloadItemState.RUNNING:
                    return '0 kiB/s'

                speed = dl_item.get_avg_download_speed()
                sz = QDownloadsTableModel._format_size(speed)

                return '{}/s'.format(sz)
            elif col == 10:
                # Progress bar
                return None
            elif col == 11:
                # Status
                handlers = QDownloadsTableModel._status_msg_handlers

                return handlers[dl_item.get_state()](dl_item)
            elif col == 12:
                return '{}x{}@{}kbps'.format(quality.xres,
                                             quality.yres,
                                             quality.bitrate // 1000)

    def headerData(self, col, ori, role):
        if ori == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return QDownloadsTableModel._HEADER[col]

        return None
