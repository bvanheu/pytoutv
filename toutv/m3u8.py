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
# DISCLAIMED. IN NO EVENT SHALL Benjamin Vanheuverzwijn BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re


SIGNATURE = '#EXTM3U'
EXT_PREFIX = '#EXT'


class Tags:

    """All possible M3U8 tags."""

    EXT_X_BYTERANGE = 'EXT-X-BYTERANGE'
    EXT_X_TARGETDURATION = 'EXT-X-TARGETDURATION'
    EXT_X_MEDIA_SEQUENCE = 'EXT-X-MEDIA-SEQUENCE'
    EXT_X_KEY = 'EXT-X-KEY'
    EXT_X_PROGRAM_DATE_TIME = 'EXT-X-PROGRAM-DATE-TIME'
    EXT_X_ALLOW_CACHE = 'EXT-X-ALLOW-CACHE'
    EXT_X_PLAYLIST_TYPE = 'EXT-X-PLAYLIST-TYPE'
    EXT_X_ENDLIST = 'EXT-X-ENDLIST'
    EXT_X_MEDIA = 'EXT-X-MEDIA'
    EXT_X_STREAM_INF = 'EXT-X-STREAM-INF'
    EXT_X_DISCONTINUITY = 'EXT-X-DISCONTINUITY'
    EXT_X_I_FRAMES_ONLY = 'EXT-X-I-FRAMES-ONLY'
    EXT_X_I_FRAME_STREAM_INF = 'EXT-X-I-FRAME-STREAM-INF'
    EXT_X_VERSION = 'EXT-X-VERSION'
    EXTINF = 'EXTINF'


class Stream:

    """An M3U8 stream."""

    BANDWIDTH = 'BANDWIDTH'
    PROGRAM_ID = 'PROGRAM-ID'
    CODECS = 'CODECS'
    RESOLUTION = 'RESOLUTION'
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'

    def __init__(self):
        self.bandwidth = None
        self.program_id = None
        self.codecs = []
        self.resolution = None
        self.audio = None
        self.video = None
        self.uri = None

    def set_attribute(self, name, value):
        if name == self.BANDWIDTH:
            self.bandwidth = int(value)
        elif name == self.PROGRAM_ID:
            self.program_id = value
        elif name == self.CODECS:
            self.codecs.append(value)
        elif name == self.RESOLUTION:
            self.resolution = value
        elif name == self.AUDIO:
            self.audio = value
        elif name == self.VIDEO:
            self.video = value

    def set_uri(self, uri):
        self.uri = uri


class Key:

    """An M3U8 cryptographic key."""

    METHOD = 'METHOD'
    URI = 'URI'
    IV = 'IV'

    def __init__(self):
        self.method = None
        self.uri = None
        self.iv = None

    def set_attribute(self, name, value):
        if name == self.METHOD:
            self.method = value
        elif name == self.URI:
            self.uri = value
        elif name == self.IV:
            self.iv = value


class Segment:

    """An M3U8 segment."""

    def __init__(self):
        self.key = None
        self.duration = None
        self.title = None
        self.uri = None

    def is_encrypted(self):
        return self.key is not None


class Playlist:

    """An M3U8 playlist."""

    def __init__(self, target_duration, media_sequence, allow_cache,
                 playlist_type, version, streams, segments):
        self.target_duration = target_duration
        self.media_sequence = media_sequence
        self.allow_cache = allow_cache
        self.playlist_type = playlist_type
        self.version = version
        self.streams = streams
        self.segments = segments


def _validate(lines):
    return lines[0].strip() == SIGNATURE


def _get_line_tagname_attributes(line):
    if ':' not in line:
        return (line[1:], '')
    tagname, attributes = line.split(':', 1)

    # Remove the '#'
    tagname = tagname[1:]

    return tagname, attributes


def _line_is_tag(line):
    return line[0:4] == EXT_PREFIX


def _line_is_relative_uri(line):
    return line[0:4] != 'http'


def parse(data, base_uri):
    streams = []
    segments = []
    current_key = None
    allow_cache = False
    target_duration = 0
    media_sequence = 0
    version = 0
    playlist_type = None
    lines = data.split('\n')

    if not _validate(lines):
        raise RuntimeError('Invalid M3U8 file: "{}"'.format(lines[0]))

    for count in range(1, len(lines)):
        line = lines[count]
        if not _line_is_tag(line):
            continue

        tagname, attributes = _get_line_tagname_attributes(line)

        if tagname == Tags.EXT_X_TARGETDURATION:
            target_duration = int(attributes)
        elif tagname == Tags.EXT_X_MEDIA_SEQUENCE:
            media_sequence = int(attributes)
        elif tagname == Tags.EXT_X_KEY:
            current_key = Key()

            # TODO: do not use split since a URL may contain ','
            attributes = attributes.split(',', 1)
            for attribute in attributes:
                name, value = attribute.split('=', 1)
                name = name.strip()
                value = value.strip('"').strip()
                current_key.set_attribute(name, value)
        elif tagname == Tags.EXT_X_ALLOW_CACHE:
            allow_cache = (attributes.strip() == 'YES')
        elif tagname == Tags.EXT_X_PLAYLIST_TYPE:
            playlist_type = attributes.strip()
        elif tagname == Tags.EXT_X_STREAM_INF:
            # Will match <PROGRAM-ID=1,BANDWIDTH=461000,RESOLUTION=480x270,CODECS="avc1.66.30, mp4a.40.5">
            regex = r'([\w-]+=(?:[a-zA-Z0-9]|"[a-zA-Z0-9,. ]*")+),?'
            attributes = re.findall(regex, attributes)

            stream = Stream()
            for attribute in attributes:
                name, value = attribute.split('=')
                name = name.strip()
                value = value.strip()
                stream.set_attribute(name, value)
            stream.uri = lines[count + 1]
            if _line_is_relative_uri(stream.uri):
                stream.uri = '/'.join([base_uri, stream.uri])
            streams.append(stream)
        elif tagname == Tags.EXT_X_VERSION:
            version = attributes
        elif tagname == Tags.EXTINF:
            duration, title = attributes.split(',')
            segment = Segment()
            segment.key = current_key
            segment.duration = float(duration.strip())
            segment.title = title.strip()
            segment.uri = lines[count + 1]
            if _line_is_relative_uri(segment.uri):
                segment.uri = '/'.join([base_uri, segment.uri])
            segments.append(segment)
        else:
            # Ignore as specified in the RFC
            continue

    return Playlist(target_duration, media_sequence, allow_cache,
                    playlist_type, version, streams, segments)
