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

import re
import os
import errno
import struct
import logging
import requests
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

    def __init__(self):
        super().__init__('File exists')


class NoSpaceLeftError(DownloadError):

    def __init__(self):
        super().__init__('No space left on device')


class Downloader:
    _seg_aes_iv = struct.Struct('>IIII')

    def __init__(self, episode, bitrate, output_dir=os.getcwd(),
                 filename=None, on_progress_update=None,
                 on_dl_start=None, overwrite=False, proxies=None,
                 timeout=15):
        self._logger = logging.getLogger(__name__)
        self._episode = episode
        self._bitrate = bitrate
        self._output_dir = output_dir
        self._filename = filename
        self._on_progress_update = on_progress_update
        self._on_dl_start = on_dl_start
        self._overwrite = overwrite
        self._proxies = proxies
        self._timeout = timeout
        self._key = None

        self._set_output_path()

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
            raise toutv.exceptions.RequestTimeoutError(url, timeout)
        except requests.exceptions.ConnectionError as e:
            raise toutv.exceptions.NetworkError() from e

        return r

    def _gen_filename(self):
        # remove illegal characters from filename
        emission_title = self._episode.get_emission().Title
        episode_title = self._episode.Title

        if self._episode.SeasonAndEpisode is not None:
            sae = self._episode.SeasonAndEpisode
            episode_title = '{} {}'.format(sae, episode_title)

        br = self._bitrate // 1000
        episode_title = '{} {}kbps'.format(episode_title, br)
        filename = '{}.{}.ts'.format(emission_title, episode_title)
        regex = r'[^ \'a-zA-Z0-9áàâäéèêëíìîïóòôöúùûüÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜçÇ()._-]'
        filename = re.sub(regex, '', filename)
        filename = re.sub(r'\s', '.', filename)

        return filename

    def _set_output_path(self):
        # create output directory if it doesn't exist
        try:
            os.makedirs(self._output_dir)
        except:
            pass

        # generate a filename if not specified by user
        if self._filename is None:
            self._filename = self._gen_filename()

        # set output path
        self._output_path = os.path.join(self._output_dir, self._filename)

    def _init_download(self):
        # prevent overwriting
        if not self._overwrite and os.path.exists(self._output_path):
            raise FileExistsError()

        pl, cookies = self._episode.get_playlist_cookies()
        self._playlist = pl
        self._cookies = cookies
        self._done_bytes = 0
        self._done_segments = 0
        self._done_segments_bytes = 0
        self._do_cancel = False

    @property
    def filename(self):
        return self._filename

    @property
    def output_path(self):
        return self._output_path

    @property
    def output_dir(self):
        return self._output_dir

    def cancel(self):
        self._logger.info('cancelling download')
        self._do_cancel = True

    def _notify_dl_start(self):
        if self._on_dl_start:
            self._on_dl_start(self._filename, self._total_segments)

    def _notify_progress_update(self):
        if self._on_progress_update:
            self._on_progress_update(self._done_segments,
                                     self._done_bytes,
                                     self._done_segments_bytes)

    def _get_segment_file_path(self, segindex):
        fmt = '.toutv-{}-{}-{}-{}.ts'
        segname = fmt.format(self._episode.get_emission().get_id(),
                             self._episode.get_id(), self._bitrate, segindex)

        return os.path.join(self._output_dir, segname)

    def _download_segment(self, segindex):
        self._logger.debug('downloading segment {}'.format(segindex))

        # segment already downloaded? skip
        segpath = self._get_segment_file_path(segindex)
        partpath = segpath + '.part'
        self._logger.debug('partial segment file path: "{}"'.format(partpath))
        self._logger.debug('segment file path: "{}"'.format(segpath))

        if os.path.isfile(segpath):
            self._logger.debug('segment file exists; skipping')
            statinfo = os.stat(segpath)
            self._done_bytes += statinfo.st_size
            return

        segment = self._segments[segindex]
        count = segindex + 1
        r = self._do_request(segment.uri, stream=True)
        encrypted_ts_segment = bytearray()
        chunks_count = 0

        for chunk in r.iter_content(8192):
            if self._do_cancel:
                raise CancelledByUserError()

            encrypted_ts_segment += chunk
            self._done_bytes += len(chunk)

            if chunks_count % 32 == 0:
                self._notify_progress_update()
            chunks_count += 1

        ts_segment = None
        if self._key:
            aes_iv = Downloader._seg_aes_iv.pack(0, 0, 0, count)
            aes = AES.new(self._key, AES.MODE_CBC, aes_iv)
            ts_segment = aes.decrypt(bytes(encrypted_ts_segment))
        else:
            ts_segment = encrypted_ts_segment

        # completely write the part file first (could be interrupted)
        with open(partpath, 'wb') as f:
            self._logger.debug('writing partial segment file "{}"'.format(partpath))
            f.write(ts_segment)

        # rename part file to segment file (should be atomic)
        os.rename(partpath, segpath)

    def _download_segment_with_retry(self, segindex, num_tries=3):
        for i in range(num_tries):
            try:
                return self._download_segment(segindex)
            except toutv.exceptions.NetworkError:
                # If it was our last retry, give up and propagate the exception.
                if i + 1 == num_tries:
                    raise

    def _get_video_stream(self):
        for stream in self._playlist.streams:
            if stream.bandwidth == self._bitrate:
                return stream

        raise DownloadError('Cannot find stream for bitrate {} bps'.format(self._bitrate))

    def _stitch_segment_files(self):
        self._logger.debug('stitching {} segment files'.format(len(self._segments)))
        part_output_path = self._output_path + '.part'

        with open(part_output_path, 'wb') as of:
            for segindex in range(len(self._segments)):
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
        except:
            # not the end of the world...
            self._logger.warn('cannot remove segment file "{}"'.format(segpath))

    def _remove_segment_files(self):
        self._logger.debug('removing {} segment files'.format(len(self._segments)))

        for segindex in range(len(self._segments)):
            self._remove_segment_file(segindex)

    def download(self):
        self._logger.debug('starting download')
        self._logger.debug('episode: {}'.format(self._episode))
        self._logger.debug('bitrate: {}'.format(self._bitrate))
        self._logger.debug('output path: {}'.format(self._output_path))
        self._logger.debug('overwrite: {}'.format(self._overwrite))
        self._logger.debug('timeout: {}'.format(self._timeout))
        self._init_download()

        # select appropriate stream for required bitrate
        stream = self._get_video_stream()

        # get video playlist
        r = self._do_request(stream.uri)
        m3u8_file = r.text
        self._video_playlist = toutv.m3u8.parse(m3u8_file,
                                                os.path.dirname(stream.uri))
        self._segments = self._video_playlist.segments
        self._total_segments = len(self._segments)
        self._logger.debug('parsed M3U8 file: {} total segments'.format(self._total_segments))

        # get decryption key
        if self._segments[0].key:
            uri = self._segments[0].key.uri
            r = self._do_request(uri)
            self._key = r.content
            self._logger.debug('decryption key: {}'.format(self._key))
        else:
            self._logger.debug('no decryption key found')

        # download segments
        self._notify_dl_start()
        self._notify_progress_update()

        for segindex in range(len(self._segments)):
            try:
                self._download_segment_with_retry(segindex)
            except Exception as e:
                if type(e) is OSError and e.errno == errno.ENOSPC:
                    raise NoSpaceLeftError()

                raise DownloadError('Cannot download segment {}: {}'.format(segindex + 1, e))

            self._done_segments += 1
            self._done_segments_bytes = self._done_bytes
            self._notify_progress_update()

        # stitch individual segment files as a complete file
        try:
            self._stitch_segment_files()
        except Exception as e:
            if type(e) is OSError and e.errno == errno.ENOSPC:
                raise NoSpaceLeftError()

            raise DownloadError('Cannot stitch segment files: {}'.format(e))

        # remove segment files
        self._remove_segment_files()
