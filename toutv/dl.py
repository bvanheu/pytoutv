# Copyright (c) 2012, Benjamin Vanheuverzwijn <bvanheu@gmail.com>
# Copyright (c) 2014, Philippe Proulx <eepp.ca>
# All rights reserved.
#
# Thanks to Marc-Etienne M. Leveille
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of pytoutv nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Benjamin Vanheuverzwijn OR Philippe Proulx
# BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import errno
import struct
import logging
import requests
import functools
from Crypto.Cipher import AES
import toutv.config
import toutv.exceptions
import toutv.m3u8


class DownloadError(RuntimeError):

    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg


class CancelledByUserError(DownloadError):

    def __init__(self):
        super().__init__('Download cancelled by user')


class FileExistsError(DownloadError):

    def __init__(self, path):
        super().__init__('File {} exists'.format(path))
        self._path = path

    @property
    def path(self):
        return self._path


class NoSpaceLeftError(DownloadError):

    def __init__(self):
        super().__init__('No space left on device')


class SegmentHandler:

    def initialize(self):
        """Called once before the Downloader tries to download any segment."""
        raise NotImplementedError()

    def has_segment(self, segindex):
        """Return whether the segment handler already has segment with index segindex.

        If the handler returns False, the Downloader will skip downloading
        this segment and call the segment_size method to determine the size
        of this segment.
        """
        raise NotImplementedError()

    def segment_size(self, segindex):
        """Return the size of segment with index segindex.

        This is called by the Downloader when the handler has indicated it
        already has a particular segment.
        """
        raise NotImplementedError()

    def on_segment(self, segindex, segment):
        """Called once for each downloaded segment.

        This method is not called for segments for which the has_segment
        returned True.
        """
        raise NotImplementedError()

    def finalize(self, num_segments):
        """Called once all the segments have been successfully downloaded."""
        raise NotImplementedError()


class FilesystemSegmentHandler(SegmentHandler):
    """SegmentHandler implementation which saves the episode on the filesystem."""

    def __init__(self,
                 episode,
                 bitrate,
                 output_dir,
                 filename,
                 overwrite=False):
        self._episode = episode
        self._bitrate = bitrate
        self._output_dir = output_dir
        self._overwrite = overwrite

        self._filename = filename
        self._output_path = os.path.join(self._output_dir, self._filename)

        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def filename(self):
        return self._filename

    @property
    def output_path(self):
        return self._output_path

    @property
    def output_dir(self):
        return self._output_dir

    def _get_segment_file_path(self, segindex):
        fmt = '.toutv-{}-{}-{}-{}.ts'
        segname = fmt.format(self._episode.get_emission().get_id(),
                             self._episode.get_id(),
                             self._bitrate,
                             segindex)

        return os.path.join(self._output_dir, segname)

    def _stitch_segment_files(self, num_segments):
        self._logger.debug('stitching {} segment files'.format(num_segments))
        part_output_path = self._output_path + '.part'

        with open(part_output_path, 'wb') as of:
            for segindex in range(num_segments):
                segpath = self._get_segment_file_path(segindex)

                if not os.path.isfile(segpath):
                    raise DownloadError('Cannot find segment file "{}"'.format(segpath))

                with open(segpath, 'rb') as segf:
                    self._logger.debug('concatenating segment file "{}"'.format(segpath))
                    of.write(segf.read())

        os.rename(part_output_path, self._output_path)

    def _remove_segment_file(self, segindex):
        segpath = self._get_segment_file_path(segindex)
        self._logger.debug('removing segment file "{}"'.format(segpath))

        try:
            os.remove(segpath)
        except Exception:
            # not the end of the world...
            self._logger.warn('cannot remove segment file "{}"'.format(segpath))

    def _remove_segment_files(self, num_segments):
        self._logger.debug('removing {} segment files'.format(num_segments))

        for segindex in range(num_segments):
            self._remove_segment_file(segindex)

    def initialize(self):
        self._logger.debug('episode: {}'.format(self._episode))
        self._logger.debug('bitrate: {}'.format(self._bitrate))
        self._logger.debug('output path: {}'.format(self._output_path))
        self._logger.debug('overwrite: {}'.format(self._overwrite))

        # Ensure the output directory exists.
        os.makedirs(self._output_dir, exist_ok=True)

        # prevent overwriting
        if not self._overwrite and os.path.exists(self._output_path):
            raise FileExistsError(self._output_path)

    def has_segment(self, segindex):
        segpath = self._get_segment_file_path(segindex)

        self._logger.debug('segment file path: "{}"'.format(segpath))

        return os.path.isfile(segpath)

    def segment_size(self, segindex):
        segpath = self._get_segment_file_path(segindex)
        statinfo = os.stat(segpath)
        return statinfo.st_size

    def on_segment(self, segindex, segment):
        segpath = self._get_segment_file_path(segindex)
        partpath = segpath + '.part'

        try:
            # completely write the part file first (could be interrupted)
            with open(partpath, 'wb') as f:
                self._logger.debug('writing partial segment file "{}"'.format(partpath))
                f.write(segment)

            # rename part file to segment file (should be atomic)
            os.rename(partpath, segpath)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                raise NoSpaceLeftError()
            else:
                raise

    def finalize(self, num_segments):
        try:
            # stitch individual segment files as a complete file
            self._stitch_segment_files(num_segments)

            # remove segment files
            self._remove_segment_files(num_segments)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                raise NoSpaceLeftError()
            else:
                raise


class SegmentProvider:

    def __init__(self):
        self.cancel = False

    def initialize(self):
        raise NotImplementedError()

    def num_segments(self):
        raise NotImplementedError()

    def download_segment(self, segindex, progress):
        raise NotImplementedError()

    def finalize(self):
        raise NotImplementedError()


class ToutvApiSegmentProvider(SegmentProvider):
    """Segment provider that fetches segments using the Tou.tv API"""

    _seg_aes_iv = struct.Struct('>IIII')

    def __init__(self, episode, bitrate, proxies=None, timeout=15):
        super().__init__()

        self._episode = episode
        self._bitrate = bitrate
        self._proxies = proxies
        self._timeout = timeout

        self._cookies = None
        self._video_playlist = None
        self._segments = None
        self._key = None

        self._logger = logging.getLogger(self.__class__.__name__)

    def _do_request(self, url, params=None, stream=False):
        self._logger.debug('HTTP GET request @ {}'.format(url))

        try:
            r = requests.get(url, params=params, headers=toutv.config.HEADERS,
                             proxies=self._proxies, cookies=self._cookies,
                             timeout=self._timeout, stream=stream)

            if r.status_code != 200:
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url,
                                                                     r.status_code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, self._timeout)
        except requests.exceptions.ConnectionError as e:
            raise toutv.exceptions.NetworkError() from e

        return r

    @staticmethod
    def _get_video_stream(playlist, bitrate):
        for stream in playlist.streams:
            if stream.bandwidth == bitrate:
                return stream

        raise DownloadError('Cannot find stream for bitrate {} bps'.format(bitrate))

    def _download_segment(self, segindex, progress):
        self._logger.debug('downloading segment {}'.format(segindex))

        encrypted_ts_segment = bytearray()
        chunks_count = 0
        num_bytes = 0

        # Obtain the URI to download this segment.
        segment = self._segments[segindex]
        request = self._do_request(segment.uri, stream=True)

        # Fetch by chunks of 8 kiB
        for chunk in request.iter_content(8192):
            if self.cancel:
                raise CancelledByUserError()

            encrypted_ts_segment += chunk
            num_bytes += len(chunk)

            # Every 32 chunks (256 kiB), we notify of our progress.
            if chunks_count % 32 == 0:
                progress(num_bytes)

            chunks_count += 1

        # We have the whole segment, decrypt it if needed.
        if self._key:
            aes_iv = self._seg_aes_iv.pack(0, 0, 0, segindex + 1)
            aes = AES.new(self._key, AES.MODE_CBC, aes_iv)
            ts_segment = aes.decrypt(bytes(encrypted_ts_segment))
        else:
            ts_segment = bytes(encrypted_ts_segment)

        return ts_segment

    def _download_segment_with_retry(self, segindex, progress, num_tries=3):
        for i in range(num_tries):
            try:
                return self._download_segment(segindex, progress)
            except toutv.exceptions.NetworkError:
                # If it was our last retry, give up and propagate the exception.
                if i + 1 == num_tries:
                    raise

    def initialize(self):
        self._logger.debug('episode: {}'.format(self._episode))
        self._logger.debug('bitrate: {}'.format(self._bitrate))
        self._logger.debug('timeout: {}'.format(self._timeout))

        playlist, cookies = self._episode.get_playlist_cookies()
        self._cookies = cookies

        # select appropriate stream for required bitrate
        stream = self._get_video_stream(playlist, self._bitrate)

        # get video playlist
        m3u8_file = self._do_request(stream.uri).text
        self._video_playlist = toutv.m3u8.parse(m3u8_file,
                                                os.path.dirname(stream.uri))
        self._segments = self._video_playlist.segments
        self._logger.debug('parsed M3U8 file: {} total segments'.format(self.num_segments()))

        # get decryption key
        if self._segments[0].key:
            uri = self._segments[0].key.uri
            self._key = self._do_request(uri).content
            self._logger.debug('decryption key: {}'.format(self._key))
        else:
            self._logger.debug('no decryption key found')

    def num_segments(self):
        return len(self._segments)

    def download_segment(self, segindex, progress):
        return self._download_segment_with_retry(segindex, progress)

    def finalize(self):
        pass


class Downloader:

    def __init__(self,
                 seg_provider,
                 seg_handler,
                 on_progress_update=None,
                 on_dl_start=None):
        self._seg_provider = seg_provider
        self._seg_handler = seg_handler

        self._on_progress_update = on_progress_update
        self._on_dl_start = on_dl_start

        self._do_cancel = False
        self._logger = logging.getLogger(self.__class__.__name__)

    def cancel(self):
        self._logger.info('cancelling download')
        self._seg_provider.cancel = True
        self._do_cancel = True

    def _notify_dl_start(self, num_segments):
        if self._on_dl_start:
            self._on_dl_start(num_segments)

    def _notify_progress_update(self, num_completed_segments, num_bytes,
                                num_bytes_partial_segment):
        if self._on_progress_update:
            self._on_progress_update(num_completed_segments, num_bytes,
                                     num_bytes_partial_segment)

    def download(self):
        self._logger.debug('starting download')

        self._seg_handler.initialize()
        self._seg_provider.initialize()

        # Get the number of segments.
        num_segments = self._seg_provider.num_segments()

        # Notify of the download start.
        self._notify_dl_start(num_segments)

        # Do an initial progress update before we begin.
        self._notify_progress_update(0, 0, 0)

        # Number of bytes in the completely downloaded segments.
        done_segment_bytes = 0

        try:
            for segindex in range(num_segments):

                if self._do_cancel:
                    raise CancelledByUserError()

                if self._seg_handler.has_segment(segindex):
                    self._logger.debug('segment handler already has segment; skipping')
                    done_segment_bytes += self._seg_handler.segment_size(segindex)
                    continue

                # Function called by the segment provider to notify of progress
                # during the fetching of a segment.
                progress = functools.partial(self._notify_progress_update,
                                             segindex, done_segment_bytes)

                # Get the segment.
                segment = self._seg_provider.download_segment(segindex, progress)

                # Update running sum of bytes.
                done_segment_bytes += len(segment)

                # Notify of progress.
                self._notify_progress_update(segindex + 1, done_segment_bytes, 0)

                # Do something with the segment.
                self._seg_handler.on_segment(segindex, segment)

            # All the segments were fetched.
            self._seg_provider.finalize()
            self._seg_handler.finalize(num_segments)
        except DownloadError as e:
            # If the exception is already a DownloadError, just propagate it...
            raise e
        except Exception as e:
            # ... otherwise, throw a DownloadError from the original exception.
            tmpl = 'Download error: {}'
            raise DownloadError(tmpl.format(e)) from e
