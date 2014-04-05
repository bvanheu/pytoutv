import time
import queue
import logging
import datetime
from PyQt4 import Qt
from PyQt4 import QtCore

from toutv import dl


class _DownloadWork:
    def __init__(self, episode, bitrate, output_dir, proxies):
        self._episode = episode
        self._bitrate = bitrate
        self._output_dir = output_dir
        self._proxies = proxies

    def get_episode(self):
        return self._episode

    def get_bitrate(self):
        return self._bitrate

    def get_output_dir(self):
        return self._output_dir

    def get_proxies(self):
        return self._proxies


class _DownloadWorkProgress:
    def __init__(self, done_segments=0, done_bytes=0):
        self._done_segments = done_segments
        self._done_bytes = done_bytes

    def get_done_segments(self):
        return self._done_segments

    def get_done_bytes(self):
        return self._done_bytes


class _QDownloadStartEvent(Qt.QEvent):
    """Event sent to download workers to make them initiate a download."""

    def __init__(self, type, work):
        super().__init__(type)

        self._work = work

    def get_work(self):
        return self._work


class _QDownloadWorker(Qt.QObject):
    download_started = QtCore.pyqtSignal(object, object, str, int)
    download_progress = QtCore.pyqtSignal(object, object)
    download_finished = QtCore.pyqtSignal(object)
    download_error = QtCore.pyqtSignal(object, object)

    def __init__(self, download_event_type, i):
        super().__init__()
        self._download_event_type = download_event_type
        self._current_work = None

    def do_work(self, work):
        self._current_work = work

        episode = work.get_episode()
        bitrate = work.get_bitrate()
        output_dir = work.get_output_dir()
        proxies = work.get_proxies()

        downloader = dl.Downloader(episode, bitrate=bitrate,
                                   output_dir=output_dir,
                                   on_dl_start=self._on_dl_start,
                                   on_progress_update=self._on_progress_update,
                                   overwrite=True, proxies=proxies)
        try:
            downloader.download()
        except Exception as e:
            self.download_error.emit(work, e)
            return

        self.download_finished.emit(work)

    def _on_dl_start(self, filename, total_segments):
        progress = _DownloadWorkProgress()
        self.download_started.emit(self._current_work, progress, filename,
                                   total_segments)

    def _on_progress_update(self, done_segments, done_bytes):
        dl_progress = _DownloadWorkProgress(done_segments, done_bytes)
        self.download_progress.emit(self._current_work, dl_progress)

    def _handle_download_event(self, ev):
        self.do_work(ev.get_work())

    def customEvent(self, ev):
        if ev.type() == self._download_event_type:
            self._handle_download_event(ev)
        else:
            logging.error("Shouldn't be here")


class QDownloadManager(Qt.QObject):
    download_created = QtCore.pyqtSignal(object)
    download_started = QtCore.pyqtSignal(object, object, str, int)
    download_progress = QtCore.pyqtSignal(object, object)
    download_finished = QtCore.pyqtSignal(object)
    download_error = QtCore.pyqtSignal(object, object)

    def __init__(self, nb_threads=5):
        super().__init__()

        self._download_event_type = Qt.QEvent.registerEventType()
        self._setup_threads(nb_threads)

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
            worker.download_error.connect(self._on_worker_error)

            # Connect worker's signals directly to our signals
            worker.download_error.connect(self.download_error)
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

    def download(self, episode, bitrate, output_dir, proxies):
        work = _DownloadWork(episode, bitrate, output_dir, proxies)

        self.download_created.emit(work)
        self._works.put(work)
        self._do_next_work()

    def _on_worker_finished(self, work):
        worker = self.sender()

        self._available_workers.put(worker)
        self._do_next_work()

    def _on_worker_error(self, work, ex):
        self._on_worker_finished(work)
