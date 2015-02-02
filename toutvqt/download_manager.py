import queue
import logging
from PyQt4 import Qt
from PyQt4 import QtCore
from toutv import dl


class _DownloadWork:
    def __init__(self, episode, quality, output_dir, proxies):
        self._episode = episode
        self._quality = quality
        self._output_dir = output_dir
        self._proxies = proxies
        self._cancelled = False

    def get_episode(self):
        return self._episode

    @property
    def quality(self):
        return self._quality

    def get_output_dir(self):
        return self._output_dir

    def get_proxies(self):
        return self._proxies

    def cancel(self):
        self._cancelled = True

    def is_cancelled(self):
        return self._cancelled


class _DownloadWorkProgress:
    def __init__(self, done_segments=0, done_bytes=0, done_segments_bytes=0):
        self._done_segments = done_segments
        self._done_bytes = done_bytes
        self._done_segments_bytes = done_segments_bytes

    def get_done_segments(self):
        return self._done_segments

    def get_done_bytes(self):
        return self._done_bytes

    def get_done_segments_bytes(self):
        return self._done_segments_bytes


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
    download_cancelled = QtCore.pyqtSignal(object)
    download_error = QtCore.pyqtSignal(object, object)

    def __init__(self, download_event_type, i):
        super().__init__()
        self._download_event_type = download_event_type
        self._current_work = None
        self._downloader = None
        self._cancelled = False

    def cancel_current_work(self):
        if self._downloader is not None:
            episode = self._current_work.get_episode()
            bitrate = self._current_work.quality.bitrate
            tmpl = 'Cancelling download of "{}" @ {} bps'
            logging.debug(tmpl.format(episode.get_title(), bitrate))
            self._downloader.cancel()

    def cancel_all_works(self):
        self._cancelled = True
        self.cancel_current_work()

    def do_work(self, work):
        if self._cancelled:
            return

        if work.is_cancelled():
            return

        self._current_work = work

        episode = work.get_episode()
        bitrate = work.quality.bitrate
        output_dir = work.get_output_dir()
        proxies = work.get_proxies()

        downloader = dl.Downloader(episode, bitrate=bitrate,
                                   output_dir=output_dir,
                                   on_dl_start=self._on_dl_start,
                                   on_progress_update=self._on_progress_update,
                                   overwrite=True, proxies=proxies)
        self._downloader = downloader

        tmpl = 'Starting download of "{}" @ {} bps'
        logging.debug(tmpl.format(episode.get_title(), bitrate))
        try:
            downloader.download()
        except dl.CancelledByUserError as e:
            self._downloader = None
            self.download_cancelled.emit(work)
            return
        except Exception as e:
            self._downloader = None
            title = episode.get_title()
            tmpl = 'Cannot download "{}" @ {} bps: {}'
            logging.error(tmpl.format(title, bitrate, e))
            self.download_error.emit(work, e)
            return

        self._downloader = None
        self.download_finished.emit(work)

    def _on_dl_start(self, filename, total_segments):
        progress = _DownloadWorkProgress()
        self.download_started.emit(self._current_work, progress, filename,
                                   total_segments)

    def _on_progress_update(self, done_segments, done_bytes,
                            done_segments_bytes):
        dl_progress = _DownloadWorkProgress(done_segments, done_bytes,
                                            done_segments_bytes)
        self.download_progress.emit(self._current_work, dl_progress)

    def _handle_download_event(self, ev):
        self.do_work(ev.get_work())

    def customEvent(self, ev):
        if ev.type() == self._download_event_type:
            self._handle_download_event(ev)
        else:
            logging.error('Download worker received wrong custom event')


class QDownloadManager(Qt.QObject):
    download_created = QtCore.pyqtSignal(object)
    download_started = QtCore.pyqtSignal(object, object, str, int)
    download_progress = QtCore.pyqtSignal(object, object)
    download_finished = QtCore.pyqtSignal(object)
    download_error = QtCore.pyqtSignal(object, object)
    download_cancelled = QtCore.pyqtSignal(object)

    def __init__(self, nb_threads=5):
        super().__init__()

        self._download_event_type = Qt.QEvent.registerEventType()
        self._setup_threads(nb_threads)

    def exit(self):
        # Cancel all workers
        logging.debug('Cancelling all download workers')
        for worker in self._workers:
            worker.cancel_all_works()

        # Clear works
        logging.debug('Clearing remaining download works')
        while not self._works.empty():
            self._works.get()

        # Join threads
        for thread in self._threads:
            logging.debug('Joining one download thread')
            thread.quit()
            thread.wait()

    def cancel_work(self, work):
        if work not in self._works_workers:
            work.cancel()
            self.download_cancelled.emit(work)
        else:
            worker = self._works_workers[work]
            worker.cancel_current_work()

    def _setup_threads(self, nb_threads):
        self._available_workers = queue.Queue()
        self._threads = []
        self._workers = []
        self._works_workers = {}
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
            worker.download_cancelled.connect(self._on_worker_finished)

            # Connect worker's signals directly to our signals
            worker.download_cancelled.connect(self.download_cancelled)
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

        self._works_workers[work] = worker
        ev = _QDownloadStartEvent(self._download_event_type, work)
        Qt.QCoreApplication.postEvent(worker, ev)

    def download(self, episode, quality, output_dir, proxies):
        work = _DownloadWork(episode, quality, output_dir, proxies)

        self.download_created.emit(work)
        self._works.put(work)
        self._do_next_work()

    def _on_worker_finished(self, work):
        title = work.get_episode().get_title()
        br = work.quality.bitrate
        logging.debug('Download of "{}" @ {} bps ended'.format(title, br))
        worker = self.sender()

        del self._works_workers[work]
        self._available_workers.put(worker)
        self._do_next_work()

    def _on_worker_error(self, work, ex):
        self._on_worker_finished(work)
