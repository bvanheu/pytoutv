# Copyright (c) 2016, Philippe Proulx <eepp.ca>
# Copyright (c) 2012, Benjamin Vanheuverzwijn <bvanheu@gmail.com>
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

import re
import os
import errno
import struct
import toutv3
import logging
import os.path
from toutv3 import playlist
from Crypto.Cipher import AES
from collections import namedtuple


_logger = logging.getLogger(__name__)


DownloadProgress = namedtuple('DownloadProgress', ['done_bytes', 'done_segments', 'total_segments', 'done_seconds'])


_seg_aes_iv = struct.Struct('>IIII')


class Download:
    def __init__(self, agent, playlist):
        self._agent = agent
        self._playlist = playlist

    def _init_download(self):
        self._done_bytes = 0
        self._done_segments = 0
        self._done_seconds = 0

    @property
    def done_bytes(self):
        return self._done_bytes

    @property
    def done_segments(self):
        return self._done_segments

    def _get_segment_file_path(self, ms):
        dirname = os.path.dirname(self._output_path)
        filename = os.path.basename(self._output_path)
        noext_filename = os.path.splitext(filename)[0]
        segment_filename = '.{}-{}.ts'.format(noext_filename, ms.media_sequence)

        return os.path.join(dirname, segment_filename)

    def _download_media_segment(self, ms):
        _logger.debug('Downloading segment {}'.format(ms.media_sequence))
        key = ms.key

        if key.method != playlist.KeyMethod.AES_128:
            raise toutv3.DownloadError('Unsupported key method at segment {}'.format(ms.media_sequence))

        bin_key = self._agent.get_media_segment_key(key.uri)

        # segment already downloaded? skip
        segpath = self._get_segment_file_path(ms)
        partpath = segpath + '.toutv-part'
        _logger.debug('  Partial segment file path: "{}"'.format(partpath))
        _logger.debug('  Segment file path: "{}"'.format(segpath))

        if os.path.isfile(segpath):
            _logger.debug('Segment file "{}" exists: skipping'.format(segpath))
            statinfo = os.stat(segpath)
            self._done_bytes += statinfo.st_size
            return

        encrypted_ts_segment = bytearray()

        for chunk in self._agent.akamaihd_stream_get(ms.uri, self._chunk_size):
            encrypted_ts_segment += chunk
            self._done_bytes += len(chunk)
            yield DownloadProgress(self._done_bytes, self._done_segments,
                                   len(self._playlist.media_segments),
                                   self._done_seconds)

        _logger.debug('Decrypting segment {}'.format(ms.media_sequence))
        aes_iv = _seg_aes_iv.pack(0, 0, 0, ms.media_sequence)
        aes = AES.new(bin_key, AES.MODE_CBC, aes_iv)
        ts_segment = aes.decrypt(bytes(encrypted_ts_segment))

        # completely write the part file first (could be interrupted)
        with open(partpath, 'wb') as f:
            _logger.debug('Writing partial segment file "{}"'.format(partpath))
            f.write(ts_segment)

        # rename part file to segment file (should be atomic)
        _logger.debug('Renaming "{}" -> "{}"'.format(partpath, segpath))
        os.rename(partpath, segpath)

    def _download_media_segment_with_tries(self, ms, num_tries=3):
        for i in range(num_tries):
            try:
                for progress in self._download_media_segment(ms):
                    yield progress
            except toutv3.NetworkError:
                _logger.info('Got a network error while trying to download segment')

                # if it was our last retry, give up and propagate the exception
                if i + 1 == num_tries:
                    _logger.debug('Abandoning download after {} attempts'.format(num_tries))
                    raise

                _logger.debug('Retrying to download segment')

            break

    def _stitch_segment_files(self):
        _logger.debug('Stitching {} segment files'.format(len(self._playlist.media_segments)))
        part_output_path = self._output_path + '.toutv-part'

        with open(part_output_path, 'wb') as of:
            for ms in self._playlist.media_segments:
                segpath = self._get_segment_file_path(ms)

                if not os.path.isfile(segpath):
                    _logger.error('Cannot find segment file "{}"'.format(segpath))
                    raise toutv3.DownloadError('While trying to stitch: Cannot find segment file "{}"'.format(segpath))

                with open(segpath, 'rb') as segf:
                    _logger.debug('Appending segment file "{}"'.format(segpath))
                    of.write(segf.read())

        _logger.debug('Renaming "{}" -> "{}"'.format(part_output_path, self._output_path))
        os.rename(part_output_path, self._output_path)

    def _remove_segment_file(self, ms):
        segpath = self._get_segment_file_path(ms)
        _logger.debug('Removing segment file "{}"'.format(segpath))

        try:
            os.remove(segpath)
        except Exception as e:
            # not the end of the world...
            _logger.info('Cannot remove segment file "{}": {}'.format(segpath, e))

    def _remove_segment_files(self):
        _logger.debug('Removing {} segment files'.format(len(self._playlist.media_segments)))

        for ms in self._playlist.media_segments:
            self._remove_segment_file(ms)

    def iter_download(self, output_path, chunk_size=4096):
        self._output_path = output_path
        self._chunk_size = max(4096, chunk_size)

        fmt = 'Starting download of {} segments to file "{}" with chunks of {} bytes'
        _logger.debug(fmt.format(len(self._playlist.media_segments),
                                 output_path, chunk_size))
        self._init_download()

        for ms in self._playlist.media_segments:
            try:
                for progress in self._download_media_segment_with_tries(ms):
                    yield progress
            except Exception as e:
                if type(e) is OSError and e.errno == errno.ENOSPC:
                    _logger.error('No space left on device')
                    raise toutv3.NoSpaceLeft()

                _logger.error('Cannot download segment file: {}'.format(e))
                raise toutv3.DownloadError('Cannot download segment {}: {}'.format(ms.media_sequence, e)) from e

            self._done_segments += 1

            if ms.duration is not None:
                self._done_seconds += ms.duration

        # stitch individual segment files as a complete file
        try:
            self._stitch_segment_files()
        except Exception as e:
            if type(e) is OSError and e.errno == errno.ENOSPC:
                _logger.error('No space left on device')
                raise toutv3.NoSpaceLeft()

            _logger.error('Cannot stitch segment files: {}'.format(e))
            raise toutv3.DownloadError('Cannot stitch segment files: {}'.format(e))

        # remove segment files
        self._remove_segment_files()
