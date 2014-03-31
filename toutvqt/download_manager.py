import time
import queue
import logging
from PyQt4 import Qt
from PyQt4 import QtCore
from PyQt4.Qt import QEvent

class QDownloadStartEvent(QEvent):
    """Event sent to download workers to make them initiate a download."""
    def __init__(self, type, work):
        super(QEvent, self).__init__(type)
        self.work = work

class QDownloadManager(Qt.QObject):
    def __init__(self, nb_threads=5):
        super(QDownloadManager, self).__init__()

        self._download_event_type = QEvent.registerEventType()
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
            worker = QDownloadWorker(self._download_event_type, i)
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

        ev = QDownloadStartEvent(self._download_event_type, work)
        Qt.QCoreApplication.postEvent(worker, ev)

    def download(self, episode, bitrate):
        work = (episode, bitrate)
        print('queueing work {}'.format(work))
        self._works.put(work)
        self._do_next_work()

    def _on_worker_finished(self, work):
        worker = self.sender()
        print('slot: worker {} finished work {}'.format(worker, work))
        self._available_workers.put(worker)
        self._do_next_work()


class QDownloadWorker(Qt.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, download_event_type, i):
        super(QDownloadWorker, self).__init__()
        self._download_event_type = download_event_type
        self.i = i

    def do_work(self, work):
        episode = work[0]
        bitrate = work[1]
        print('worker {} "downloading" episode {} at {}'.format(self, episode.Title, work))
        time.sleep(10)
        print('worker {} done "downloading" episode {} at {}'.format(self, episode.Title, work))
        self.finished.emit(work)

    def handle_download_event(self, ev):
        self.do_work(ev.work)

    def customEvent(self, ev):
        if ev.type() == self._download_event_type:
            self.handle_download_event(ev)
        else:
            logging.error("Shouldn't be here")

    def __str__(self):
        return "<QDownloadWorker #%d>" % (self.i)
