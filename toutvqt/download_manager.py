import time
import queue
from PyQt4 import Qt
from PyQt4 import QtCore


class QDownloadManager(Qt.QObject):
    def __init__(self, nb_threads=5):
        super(QDownloadManager, self).__init__()

        self._setup_threads(nb_threads)

    def _setup_threads(self, nb_threads):
        self._available_workers = queue.Queue()
        self._threads = []
        self._workers = []
        self._works = queue.Queue()
        for i in range(nb_threads):
            thread = Qt.QThread()
            worker = QDownloadWorker()
            self._threads.append(thread)
            self._workers.append(worker)
            self._available_workers.put(worker)
            worker.moveToThread(thread)
            worker.finished.connect(self._on_worker_finished)
            thread.start()

    def download(self, work):
        print('queueing work {}'.format(work))
        self._works.put(work)
        self._do_next_work()

    def _do_next_work(self):
        try:
            worker = self._available_workers.get_nowait()
        except queue.Empty:
            return

        try:
            work = self._works.get_nowait()
        except queue.Empty:
            return

        # TODO: asynchronously call worker.do_work(work) here

    def _on_worker_finished(self, work):
        worker = self.sender()
        print('slot: worker {} finished work {}'.format(worker, work))
        self._available_workers.put(worker)
        self._do_next_work()


class QDownloadWorker(Qt.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self):
        super(QDownloadWorker, self).__init__()

    def do_work(self, work):
        print('worker {} starting work {}'.format(self, work))
        time.sleep(10)
        print('worker {} done with work {}'.format(self, work))
        self.finished.emit(work)
