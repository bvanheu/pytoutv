import time
import queue
import logging
from PyQt4 import Qt
from PyQt4 import QtCore


class _DownloadWork:
    def __init__(self, episode, bitrate):
        self._episode = episode
        self._bitrate = bitrate

    def get_episode(self):
        return self._episode

    def get_bitrate(self):
        return self._bitrate


class _QDownloadStartEvent(Qt.QEvent):
    """Event sent to download workers to make them initiate a download."""
    def __init__(self, type, work):
        super(Qt.QEvent, self).__init__(type)

        self._work = work

    def get_work(self):
        return self._work


class QDownloadManager(Qt.QObject):
    def __init__(self, nb_threads=5):
        super(QDownloadManager, self).__init__()

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
            worker.finished.connect(self._on_worker_finished)
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
        self._works.put(work)
        self._do_next_work()

    def _on_worker_finished(self, work):
        worker = self.sender()
        print('slot: worker {} finished work {}'.format(worker, work))
        self._available_workers.put(worker)
        self._do_next_work()


class _QDownloadWorker(Qt.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, download_event_type, i):
        super(_QDownloadWorker, self).__init__()
        self._download_event_type = download_event_type
        self._i = i

    def do_work(self, work):
        episode = work.get_episode()
        bitrate = work.get_bitrate()
        print('worker {} "downloading" episode {} at {}'.format(self, episode.Title, work))
        time.sleep(10)
        print('worker {} done "downloading" episode {} at {}'.format(self, episode.Title, work))
        self.finished.emit(work)

    def _handle_download_event(self, ev):
        self.do_work(ev.get_work())

    def customEvent(self, ev):
        if ev.type() == self._download_event_type:
            self._handle_download_event(ev)
        else:
            logging.error("Shouldn't be here")

    def __str__(self):
        return '<QDownloadWorker #{}>'.format(self._i)
