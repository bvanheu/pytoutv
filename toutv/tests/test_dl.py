import unittest
from toutv import dl


class DummySegmentProvider(dl.SegmentProvider):

    def __init__(self):
        self._segments = [
            b'abcd',
            b'efgh',
            b'ijkl',
            b'mnop',
        ]

    def initialize(self):
        pass

    def download_segment(self, segindex, progress):
        # Simulate that we have a partial progress update where we have
        # downloaded 2 of the 4 bytes.
        progress(2)

        return self._segments[segindex]

    def num_segments(self):
        return len(self._segments)

    def finalize(self):
        pass


class DummySegmentHandler(dl.SegmentHandler):

    def __init__(self):
        self._segments = []

    def initialize(self):
        pass

    def finalize(self, num_segments):
        pass

    def segment_size(self, segindex):
        pass

    def has_segment(self, segindex):
        return False

    def on_segment(self, segindex, segment):
        assert segindex == len(self._segments)

        self._segments.append(segment)


class DlTest(unittest.TestCase):

    def test_simple_download(self):
        seg_provider = DummySegmentProvider()
        seg_handler = DummySegmentHandler()
        downloader = dl.Downloader(seg_provider, seg_handler)
        downloader.download()
        assert seg_provider._segments == seg_handler._segments

    def test_on_progress_update(self):

        seg_provider = DummySegmentProvider()
        seg_handler = DummySegmentHandler()

        class Progress:

            _expected_values = [
                # completed segments, bytes of completed segments, bytes of current partial segment
                (0, 0, 0),
                (0, 0, 2),
                (1, 4, 0),
                (1, 4, 2),
                (2, 8, 0),
                (2, 8, 2),
                (3, 12, 0),
                (3, 12, 2),
                (4, 16, 0),
            ]

            def __init__(self):
                self._num_calls = 0

            def progress(self,
                         num_completed_segments,
                         num_bytes_completed_segments,
                         num_bytes_partial_segment):
                exp = self._expected_values[self._num_calls]
                assert exp == (num_completed_segments, num_bytes_completed_segments, num_bytes_partial_segment)
                self._num_calls += 1

        p = Progress()

        downloader = dl.Downloader(seg_provider, seg_handler, on_progress_update=p.progress)
        downloader.download()
