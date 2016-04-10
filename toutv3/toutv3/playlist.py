# Copyright (c) 2016, Philippe Proulx <eepp.ca>
# All rights reserved.
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
# DISCLAIMED. IN NO EVENT SHALL Philippe Proulx BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import enum
from collections import namedtuple


class ParseError(Exception):
    def __init__(self, msg, line):
        super().__init__(msg)
        self._line = line

    @property
    def line(self):
        return self._line


Resolution = namedtuple('Resolution', ['width', 'height'])


class VariantStream:
    def __init__(self, program_id, bandwidth, avg_bandwidth, codecs,
                 resolution, frame_rate, audio, video, subtitles,
                 closed_captions, uri):
        self._program_id = program_id
        self._bandwidth = bandwidth
        self._avg_bandwidth = avg_bandwidth
        self._codecs = codecs
        self._resolution = resolution
        self._frame_rate = frame_rate
        self._audio = audio
        self._video = video
        self._subtitles = subtitles
        self._closed_captions = closed_captions
        self._uri = uri

    @property
    def program_id(self):
        return self._program_id

    @property
    def bandwidth(self):
        return self._bandwidth

    @property
    def avg_bandwidth(self):
        return self._avg_bandwidth

    @property
    def codecs(self):
        return self._codecs

    @property
    def resolution(self):
        return self._resolution

    @property
    def frame_rate(self):
        return self._frame_rate

    @property
    def audio(self):
        return self._audio

    @property
    def video(self):
        return self._video

    @property
    def subtitles(self):
        return self._subtitles

    @property
    def closed_captions(self):
        return self._closed_captions

    @property
    def uri(self):
        return self._uri


@enum.unique
class KeyMethod(enum.Enum):
    NONE = 'NONE'
    AES_128 = 'AES-128'
    SAMPLE_AES = 'SAMPLE-AES'


class Key:
    def __init__(self, method, uri):
        self._method = method
        self._uri = uri

    @property
    def method(self):
        return self._method

    @property
    def uri(self):
        return self._uri


class MediaSegment:
    def __init__(self, media_sequence, duration, title, key, uri):
        self._media_sequence = media_sequence
        self._duration = duration
        self._title = title
        self._key = key
        self._uri = uri

    @property
    def media_sequence(self):
        return self._media_sequence

    @property
    def duration(self):
        return self._duration

    @property
    def title(self):
        return self._title

    @property
    def key(self):
        return self._key

    @property
    def uri(self):
        return self._uri


class Playlist:
    def __init__(self, target_duration, media_segments):
        self._target_duration = target_duration
        self._media_segments = media_segments

    @property
    def target_duration(self):
        return self._target_duration

    @property
    def media_segments(self):
        return self._media_segments


class MasterPlaylist:
    def __init__(self, variant_streams):
        self._variant_streams = variant_streams

    @property
    def variant_streams(self):
        return self._variant_streams


_re_attr = re.compile(r'([A-Za-z0-9_-]+)=("[^"]+"|[^,]+),?\s*')
_re_resolution = re.compile(r'(\d+)[xX](\d+)')
_re_extinf = re.compile(r'(\d+),(.*)')


def _extract_attrs(attrs_str):
    attrs = {}

    for attr_m in _re_attr.finditer(attrs_str):
        value = attr_m.group(2)

        if value[0] == '"' and value[-1] == '"':
            value = value[1:-1]

        attrs[attr_m.group(1)] = value

    return attrs


def _extract_tag_payload(line):
    pos = line.find(':')

    if pos == -1:
        return ''

    return line[pos + 1:]


def _create_variant_stream(line, uri):
    program_id = None
    bandwidth = None
    avg_bandwidth = None
    codecs = None
    resolution = None
    frame_rate = None
    audio = None
    video = None
    subtitles = None
    closed_captions = None
    attrs = _extract_attrs(_extract_tag_payload(line))

    if 'PROGRAM-ID' in attrs:
        program_id = int(attrs['PROGRAM-ID'])

    if 'AVERAGE-BANDWIDTH' in attrs:
        avg_bandwidth = int(attrs['AVERAGE-BANDWIDTH'])

    if 'BANDWIDTH' in attrs:
        bandwidth = int(attrs['BANDWIDTH'])

    if 'CODECS' in attrs:
        codecs = attrs['CODECS']

    if 'RESOLUTION' in attrs:
        m = _re_resolution.match(attrs['RESOLUTION'])

        if m:
            resolution = Resolution(m.group(1), m.group(2))

    if 'FRAME-RATE' in attrs:
        frame_rate = float(attrs['FRAME-RATE'])

    if 'AUDIO' in attrs:
        audio = attrs['AUDIO']

    if 'VIDEO' in attrs:
        video = attrs['VIDEO']

    if 'SUBTITLES' in attrs:
        subtitles = attrs['SUBTITLES']

    if 'CLOSED-CAPTIONS' in attrs:
        closed_captions = attrs['CLOSED-CAPTIONS']

    return VariantStream(program_id=program_id, avg_bandwidth=avg_bandwidth,
                         bandwidth=bandwidth, codecs=codecs,
                         resolution=resolution, frame_rate=frame_rate,
                         audio=audio, video=video, subtitles=subtitles,
                         closed_captions=closed_captions, uri=uri)


def _create_target_duration(line):
    payload = _extract_tag_payload(line)

    if not payload:
        return

    return TargetDuration(int(payload))


def _create_key(line):
    method = None
    uri = None
    attrs = _extract_attrs(_extract_tag_payload(line))

    if 'METHOD' in attrs:
        method_attr = attrs['METHOD']

        if method_attr == 'NONE':
            method = KeyMethod.NONE
        elif method_attr == 'AES-128':
            method = KeyMethod.AES_128
        elif method_attr == 'SAMPLE-AES':
            method = KeyMethod.SAMPLE_AES

    if 'URI' in attrs:
        uri = attrs['URI']

    return Key(method=method, uri=uri)


def _create_media_segment(line, key, media_sequence, uri):
    duration = None
    title = None
    m = _re_extinf.match(_extract_tag_payload(line))

    if m:
        duration = float(m.group(1))

        if m.group(2):
            title = m.group(2)

    return MediaSegment(media_sequence=media_sequence, duration=duration,
                        title=title, key=key, uri=uri)


def from_m3u8(m3u8):
    lines = m3u8.split('\n')
    tags = []
    cur_media_sequence = 0
    cur_key = None
    target_duration = None
    variant_streams = []
    media_segments = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if i == 0:
            if line != '#EXTM3U':
                raise ParseError('Expecting "#EXTM3U"', i)

            i += 1

        if line.startswith('#EXT-X-STREAM-INF'):
            uri = lines[i + 1]
            variant_stream = _create_variant_stream(line, uri)

            if variant_stream is not None:
                variant_streams.append(variant_stream
                    )
            i += 2
        elif line.startswith('#EXT-X-TARGETDURATION'):
            target_duration = _create_target_duration(line)
            i += 1
        elif line.startswith('#EXT-X-KEY'):
            cur_key = _create_key(line)
            i += 1
        elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):
            payload = _extract_tag_payload(line)

            if payload is not None:
                cur_media_sequence = int(payload)

            i += 1
        elif line.startswith('#EXTINF'):
            uri = lines[i + 1]
            media_segment = _create_media_segment(line, cur_key,
                                                  cur_media_sequence, uri)

            if media_segment is not None:
                media_segments.append(media_segment)

            i += 2
            cur_media_sequence += 1
        elif line.startswith('#EXT-X-ENDLIST'):
            # end of list
            break
        else:
            # ignore unknown tag
            i += 1

    if variant_streams:
        return MasterPlaylist(variant_streams)
    else:
        return Playlist(target_duration, media_segments)
