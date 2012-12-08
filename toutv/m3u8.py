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
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re

class M3u8_Tag():
    EXT_X_BYTERANGE = "EXT-X-BYTERANGE"
    EXT_X_TARGETDURATION = "EXT-X-TARGETDURATION"
    EXT_X_MEDIA_SEQUENCE = "EXT-X-MEDIA-SEQUENCE"
    EXT_X_KEY = "EXT-X-KEY"
    EXT_X_PROGRAM_DATE_TIME = "EXT-X-PROGRAM-DATE-TIME"
    EXT_X_ALLOW_CACHE = "EXT-X-ALLOW-CACHE"
    EXT_X_PLAYLIST_TYPE = "EXT-X-PLAYLIST-TYPE"
    EXT_X_ENDLIST = "EXT-X-ENDLIST"
    EXT_X_MEDIA = "EXT-X-MEDIA"
    EXT_X_STREAM_INF = "EXT-X-STREAM-INF"
    EXT_X_DISCONTINUITY = "EXT-X-DISCONTINUITY"
    EXT_X_I_FRAMES_ONLY = "EXT-X-I-FRAMES-ONLY"
    EXT_X_I_FRAME_STREAM_INF = "EXT-X-I-FRAME-STREAM-INF"
    EXT_X_VERSION = "EXT-X-VERSION"
    EXTINF = "EXTINF"

    def set_attribute(name, value):
        pass

class M3u8_Stream():
    BANDWIDTH = "BANDWIDTH"
    PROGRAM_ID = "PROGRAM-ID"
    CODECS = "CODECS"
    RESOLUTION = "RESOLUTION"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"

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

#
# EXT-X-KEY tag
#
class M3u8_Key:
    METHOD = "METHOD"
    URI = "URI"
    IV = "IV"

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

#
# EXTINF tag
#
class M3u8_Segment():
    def __init__(self):
        self.key = None
        self.duration = None
        self.title = None
        self.uri = None

    def is_encrypted(self):
        return self.key != None

#
# M3u8 playlist
#
class M3u8_Playlist():
    def __init__(self, target_duration, media_sequence, allow_cache, playlist_type, version, streams, segments):
        self.target_duration = target_duration
        self.media_sequence = media_sequence
        self.allow_cache = allow_cache
        self.playlist_type = playlist_type
        self.version = version
        self.streams = streams
        self.segments = segments

#
# M3U8 parser
# A better implementation:
# http://gitorious.org/hls-player/hls-player/blobs/master/HLS/m3u8.py
#
class M3u8_Parser():
    def __init__(self):
        pass

    def validate(self, lines):
        return lines[0] == "#EXTM3U"

    def parse_line(self, line):
        if ":" not in line:
            return (line[1:], "")

        (tagname, attributes) = line.split(':', 1)

        # Remove the '#'
        tagname = tagname[1:]

        return (tagname, attributes)

    def line_is_tag(self, line):
        return line[0:4] == "#EXT"

    def line_is_relative_uri(self, line):
        return line[0:4] != "http"

    def parse(self, data, base_uri):
        streams = []
        segments = []

        current_key = None

        allow_cache = False
        target_duration = 0
        media_sequence = 0
        version = 0
        playlist_type = None

        lines = data.split("\n")

        if not self.validate(lines):
            raise Exception("invalid m3u8 file <" + lines[0] + ">")

        for count in range(1, len(lines)):

            if not (self.line_is_tag(lines[count])):
                continue

            (tagname, attributes) = self.parse_line(lines[count])

            if tagname == M3u8_Tag.EXT_X_BYTERANGE:
                pass

            if tagname == M3u8_Tag.EXT_X_TARGETDURATION:
                target_duration = int(attributes)

            elif tagname == M3u8_Tag.EXT_X_MEDIA_SEQUENCE:
                media_sequence = int(attributes)

            elif tagname == M3u8_Tag.EXT_X_KEY:
                current_key = M3u8_Key()

                # TODO - we cannot use split since there could have some ',' in the url
                attributes = attributes.split(",", 1)
                for attribute in attributes:
                    (name, value) = attribute.split("=", 1)
                    current_key.set_attribute(name.strip(), value.strip('"').strip())

            elif tagname == M3u8_Tag.EXT_X_PROGRAM_DATE_TIME:
                pass

            elif tagname == M3u8_Tag.EXT_X_ALLOW_CACHE:
                allow_cache = (attributes.strip() == "YES")

            elif tagname == M3u8_Tag.EXT_X_PLAYLIST_TYPE:
                playlist_type = attributes.strip()

            elif tagname == M3u8_Tag.EXT_X_ENDLIST:
                pass

            elif tagname == M3u8_Tag.EXT_X_MEDIA:
                pass

            elif tagname == M3u8_Tag.EXT_X_STREAM_INF:
                stream = M3u8_Stream()

                # Will match <PROGRAM-ID=1,BANDWIDTH=461000,RESOLUTION=480x270,CODECS="avc1.66.30, mp4a.40.5">
                attributes = re.findall(r"([\w-]+=(?:[a-zA-Z0-9]|\"[a-zA-Z0-9,. ]*\")+),?", attributes)

                for attribute in attributes:
                    (name, value) = attribute.split("=")
                    stream.set_attribute(name.strip(), value.strip())

                stream.uri = lines[count+1]
                if self.line_is_relative_uri(stream.uri):
                    stream.uri = base_uri + "/" + stream.uri

                streams.append(stream)

            elif tagname == M3u8_Tag.EXT_X_DISCONTINUITY:
                pass

            elif tagname == M3u8_Tag.EXT_X_I_FRAMES_ONLY:
                pass

            elif tagname == M3u8_Tag.EXT_X_I_FRAME_STREAM_INF:
                pass

            elif tagname == M3u8_Tag.EXT_X_VERSION:
                version = attributes

            elif tagname == M3u8_Tag.EXTINF:
                segment = M3u8_Segment()
                (duration, title) = attributes.split(",")

                segment.key = current_key
                segment.duration = int(duration.strip())
                segment.title = title.strip()
                segment.uri = lines[count+1]
                if self.line_is_relative_uri(segment.uri):
                    segment.uri = base_uri + "/" + segment.uri

                segments.append(segment)
            else:
                # Ignore as specified in the RFC
                continue

        return M3u8_Playlist(target_duration, media_sequence, allow_cache, playlist_type, version, streams, segments)
