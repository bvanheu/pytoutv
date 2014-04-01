import time
import queue
import logging
from PyQt4 import Qt
from PyQt4 import QtCore

from toutv import dl


class _DownloadWork:

    def __init__(self, episode, bitrate):
        self._episode = episode
        self._bitrate = bitrate

    def get_episode(self):
        return self._episode

    def get_bitrate(self):
        return self._bitrate

    def __str__(self):
        return '<_DownloadWork of {} at {}>'.format(self._episode.Title,
                                                    self._bitrate)

class _DownloadWorkProgress:

    def __init__(self, done_segments_count, total_segments_count, done_bytes_count):
        self._done_segments_count = done_segments_count
        self._total_segments_count = total_segments_count
        self._done_bytes_count = done_bytes_count

    def get_total_segments_count(self):
        return self._total_segments_count

    def get_done_segments_count(self):
        return self._done_segments_count

    def get_done_bytes_count(self):
        return self._done_bytes_count

    def __str__(self):
        return '<_DownloadWorkProgress {}/{}, {} bytes>'.format(self._done_segments_count,
                                                                self._total_segments_count,
                                                                self._done_bytes_count)


class _QDownloadStartEvent(Qt.QEvent):

    """Event sent to download workers to make them initiate a download."""

    def __init__(self, type, work):
        super().__init__(type)

        self._work = work

    def get_work(self):
        return self._work


class _QDownloadWorker(Qt.QObject):

    download_started = QtCore.pyqtSignal(object, object)
    download_progress = QtCore.pyqtSignal(object, object)
    download_finished = QtCore.pyqtSignal(object)

    def __init__(self, download_event_type, i):
        super().__init__()
        self._download_event_type = download_event_type
        self._i = i
        self._current_work = None

    def do_work(self, work):
        self._current_work = work

        episode = work.get_episode()
        bitrate = work.get_bitrate()

        print('worker {} "downloading" {}'.format(self, work))

        downloader = dl.Downloader(episode, bitrate=bitrate,
                                   output_dir="/tmp",
                                   on_dl_start=self._on_dl_start,
                                   on_progress_update=self._on_progress_update,
                                   overwrite=True).download()

        print('worker {} done "downloading" {}'.format(self, work))
        self.download_finished.emit(work)

    def _on_dl_start(self, filename, total_segments_count):
        print("Started downloading {} with {} segments".format(
            filename, total_segments_count))
        progress = _DownloadWorkProgress(0, total_segments_count, 0)
        self.download_started.emit(self._current_work, progress)

    def _on_progress_update(self, segments_count, segments_count_total, bytes_count):
        print("Now at {} bytes, {} segments".format(
            bytes_count, segments_count))
        progress = _DownloadWorkProgress(segments_count, segments_count_total, bytes_count)
        self.download_progress.emit(self._current_work, progress)

    def _handle_download_event(self, ev):
        self.do_work(ev.get_work())

    def customEvent(self, ev):
        if ev.type() == self._download_event_type:
            self._handle_download_event(ev)
        else:
            logging.error("Shouldn't be here")

    def __str__(self):
        return '<QDownloadWorker #{}>'.format(self._i)


class QDownloadManager(Qt.QObject):

    download_created = QtCore.pyqtSignal(object)
    download_started = QtCore.pyqtSignal(object, object)
    download_progress = QtCore.pyqtSignal(object, object)
    download_finished = QtCore.pyqtSignal(object)

    def __init__(self, nb_threads=5):
        super().__init__()

        self._download_event_type = Qt.QEvent.registerEventType()
        self._setup_threads(nb_threads)

        self.download_created.connect(self.test_created)
        self.download_started.connect(self.test_started)
        self.download_progress.connect(self.test_progress)
        self.download_finished.connect(self.test_finished)

    def exit(self):
        # TODO: kill n wait threads
        pass

    def _setup_threads(self, nb_threads):
        self._available_workers = queue.Queue()
        self._threads = []
        self._workers = []
        self._works = queue.Queue()

        for i in range(nb_threads):
            thread = Qt.QThread()
            worker = _QDownloadWorker(self._download_event_type, i)
            self._threads.append(thread)
            self._workers.append(worker)
            self._available_workers.put(worker)
            worker.moveToThread(thread)
            worker.download_finished.connect(self._on_worker_finished)

            # Connect worker's signals directly to our signals
            worker.download_finished.connect(self.download_finished)
            worker.download_started.connect(self.download_started)
            worker.download_progress.connect(self.download_progress)

            thread.start()

    def _do_next_work(self):
        try:
            worker = self._available_workers.get_nowait()
        except queue.Empty:
            return

        try:
            work = self._works.get_nowait()
        except queue.Empty:
            self._available_workers.put(worker)
            return

        ev = _QDownloadStartEvent(self._download_event_type, work)
        Qt.QCoreApplication.postEvent(worker, ev)

    def download(self, episode, bitrate):
        work = _DownloadWork(episode, bitrate)
        print('queueing work {}'.format(work))
        self.download_created.emit(work)
        self._works.put(work)
        self._do_next_work()

    def _on_worker_finished(self, work):
        worker = self.sender()
        print('slot: worker {} finished work {}'.format(worker, work))

        self._available_workers.put(worker)
        self._do_next_work()

    def test_created(self, work):
        print('* test_created {}'.format(work))

    def test_started(self, work, progress):
        print('* test_started {} {}'.format(work, progress))

    def test_progress(self, work, progress):
        print('* test_progress {} {}'.format(work, progress))

    def test_finished(self, work):
        print('* test_finished {}'.format(work))

