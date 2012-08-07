#!/usr/bin/env python2

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


import struct
import suds
import logging
import argparse
import sys
import shelve
import textwrap
import json
import urllib2
import cookielib
import os
from Crypto.Cipher import AES

IPHONE4_USER_AGENT = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"
TOUTV_WSDL_URL = "http://api.tou.tv/v1/TouTVAPIService.svc?wsdl"
TOUTV_PLAYLIST_URL = "http://api.radio-canada.ca/validationMedia/v1/Validation.html?appCode=thePlatform&deviceType=iphone4&connectionType=wifi&idMedia=%s&output=json"

# The next license only apply for the class ProgressBar
#
# A Python Library to create a Progress Bar.
# Copyright (C) 2008  BJ Dierkes <wdierkes@5dollarwhitebox.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# This class is an improvement from the original found at:
#
#   http://code.activestate.com/recipes/168639/
#
class ProgressBar:
    def __init__(self, min_value = 0, max_value = 100, width=77,**kwargs):
        self.char = kwargs.get('char', '#')
        self.mode = kwargs.get('mode', 'dynamic') # fixed or dynamic
        if not self.mode in ['fixed', 'dynamic']:
            self.mode = 'fixed'

        self.bar = ''
        self.min = min_value
        self.max = max_value
        self.span = max_value - min_value
        self.width = width
        self.amount = 0       # When amount == max, we are 100% done
        self.update_amount(0)


    def increment_amount(self, add_amount = 1):
        """
        Increment self.amount by 'add_ammount' or default to incrementing
        by 1, and then rebuild the bar string.
        """
        new_amount = self.amount + add_amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()


    def update_amount(self, new_amount = None):
        """
        Update self.amount with 'new_amount', and then rebuild the bar
        string.
        """
        if not new_amount: new_amount = self.amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()


    def build_bar(self):
        """
        Figure new percent complete, and rebuild the bar string base on
        self.amount.
        """
        diff = float(self.amount - self.min)
        percent_done = int(round((diff / float(self.span)) * 100.0))

        # figure the proper number of 'character' make up the bar
        all_full = self.width - 2
        num_hashes = int(round((percent_done * all_full) / 100))

        if self.mode == 'dynamic':
            # build a progress bar with self.char (to create a dynamic bar
            # where the percent string moves along with the bar progress.
            self.bar = self.char * num_hashes
        else:
            # build a progress bar with self.char and spaces (to create a
            # fixe bar (the percent string doesn't move)
            self.bar = self.char * num_hashes + ' ' * (all_full-num_hashes)

        percent_str = str(percent_done) + "%"
        self.bar = '[ ' + self.bar + ' ] ' + percent_str


    def __str__(self):
        return str(self.bar)

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

                attributes = attributes.split(",")
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

class Mapper():
    def __init__(self):
        self.classes = {}
        self.classes['Emission'] = Emission
        self.classes['Genre'] = Genre
        self.classes['Episode'] = Episode
        self.classes['EmissionRepertoire'] = EmissionRepertoire
        self.classes['SearchResults'] = SearchResults
        self.classes['SearchResultData'] = SearchResultData

    def factory(self, class_type):
        return self.classes[class_type]()

class MapperSoap(Mapper):
    def dto_to_bo(self, dto, class_type):
        bo = self.factory(class_type)
        bo_vars = vars(bo)

        for key in bo_vars.keys():
            value = getattr(dto, key)

            if isinstance(value, suds.sax.text.Text):
                value = value.encode("utf-8")
            elif isinstance(value, object):
                if value.__class__.__name__ == "GenreDTO":
                    value = self.dto_to_bo(value, "Genre")
                elif value.__class__.__name__ == "EmissionDTO":
                    value = self.dto_to_bo(value, "Emission")
                elif value.__class__.__name__ == "EpisodeDTO":
                    value = self.dto_to_bo(value, "Episode")

            setattr(bo, key, value)

        return bo

class Emission():
    def __init__(self):
        self.CategoryURL = None
        self.ClassCategory = None
        self.ContainsAds = None
        self.Country = None
        self.DateRetraitOuEmbargo = None
        self.Description = None
        self.DescriptionOffline = None
        self.DescriptionUnavailable = None
        self.DescriptionUnavailableText = None
        self.DescriptionUpcoming = None
        self.DescriptionUpcomingText = None
        self.EstContenuJeunesse = None
        self.EstExclusiviteRogers = None
        self.GeoTargeting = None
        self.Genre = None
        self.Id = None
        self.ImageBackground = None
        self.ImagePromoLargeI = None
        self.ImagePromoLargeJ = None
        self.ImagePromoNormalK = None
        self.Network = None
        self.Network2 = None
        self.Network3 = None
        self.ParentId = None
        self.Partner = None
        self.PlaylistExist = None
        self.PromoDescription = None
        self.PromoTitle = None
        self.RelatedURL1 = None
        self.RelatedURL2 = None
        self.RelatedURL3 = None
        self.RelatedURL4 = None
        self.RelatedURL5 = None
        self.RelatedURLImage1 = None
        self.RelatedURLImage2 = None
        self.RelatedURLImage3 = None
        self.RelatedURLImage4 = None
        self.RelatedURLImage5 = None
        self.RelatedURLText1 = None
        self.RelatedURLText2 = None
        self.RelatedURLText3 = None
        self.RelatedURLText4 = None
        self.RelatedURLText5 = None
        self.SeasonNumber = None
        self.Show = None
        self.ShowSearch = None
        self.SortField = None
        self.SortOrder = None
        self.SubCategoryType = None
        self.Title = None
        self.TitleIndex = None
        self.Url = None
        self.Year = None

class Genre():
    def __init__(self):
        self.CategoryURL = None
        self.ClassCategory = None
        self.Description = None
        self.Id = None
        self.ImageBackground = None
        self.ParentId = None
        self.Title = None
        self.Url = None

class Episode():
    def __init__(self):
        self.AdPattern = None
        self.AirDateFormated = None
        self.AirDateLongString = None
        self.Captions = None
        self.CategoryId = None
        self.ChapterStartTimes = None
        self.ClipType = None
        self.Copyright = None
        self.Country = None
        self.DateSeasonEpisode = None
        self.Description = None
        self.DescriptionShort = None
        self.EpisodeNumber = None
        self.EstContenuJeunesse = None
        self.Event = None
        self.EventDate = None
        self.FullTitle = None
        self.GenreTitle = None
        self.Id = None
        self.ImageBackground = None
        self.ImagePlayerLargeA = None
        self.ImagePlayerNormalC = None
        self.ImagePromoLargeI = None
        self.ImagePromoLargeJ = None
        self.ImagePromoNormalK = None
        self.ImageThumbMicroG = None
        self.ImageThumbMoyenL = None
        self.ImageThumbNormalF = None
        self.IsMostRecent = None
        self.IsUniqueEpisode = None
        self.Keywords = None
        self.LanguageCloseCaption = None
        self.Length = None
        self.LengthSpan = None
        self.LengthStats = None
        self.LengthString = None
        self.LiveOnDemand = None
        self.MigrationDate = None
        self.Musique = None
        self.Network = None
        self.Network2 = None
        self.Network3 = None
        self.NextEpisodeDate = None
        self.OriginalAirDate = None
        self.PID = None
        self.Partner = None
        self.PeopleAuthor = None
        self.PeopleCharacters = None
        self.PeopleCollaborator = None
        self.PeopleColumnist = None
        self.PeopleComedian = None
        self.PeopleDesigner = None
        self.PeopleDirector = None
        self.PeopleGuest = None
        self.PeopleHost = None
        self.PeopleJournalist = None
        self.PeoplePerformer = None
        self.PeoplePersonCited = None
        self.PeopleSpeaker = None
        self.PeopleWriter = None
        self.PromoDescription = None
        self.PromoTitle = None
        self.Rating = None
        self.RelatedURL1 = None
        self.RelatedURL2 = None
        self.RelatedURL3 = None
        self.RelatedURL4 = None
        self.RelatedURL5 = None
        self.RelatedURLText1 = None
        self.RelatedURLText2 = None
        self.RelatedURLText3 = None
        self.RelatedURLText4 = None
        self.RelatedURLText5 = None
        self.RelatedURLimage1 = None
        self.RelatedURLimage2 = None
        self.RelatedURLimage3 = None
        self.RelatedURLimage4 = None
        self.RelatedURLimage5 = None
        self.SeasonAndEpisode = None
        self.SeasonAndEpisodeLong = None
        self.SeasonNumber = None
        self.Show = None
        self.ShowSearch = None
        self.ShowSeasonSearch = None
        self.StatusMedia = None
        self.Subtitle = None
        self.Team1CountryCode = None
        self.Team2CountryCode = None
        self.Title = None
        self.TitleID = None
        self.TitleSearch = None
        self.Url = None
        self.UrlEmission = None
        self.Year = None
        self.iTunesLinkUrl = None

class EmissionRepertoire():
    def __init__(self):
        self.AnneeProduction = None
        self.CategorieDuree = None
        self.DateArrivee = None
        self.DateDepart = None
        self.DateRetraitOuEmbargo = None
        self.DescriptionUnavailableText = None
        self.DescriptionUpcomingText = None
        self.Genre = None
        self.Id = None
        self.ImagePromoNormalK = None
        self.IsGeolocalise = None
        self.NombreEpisodes = None
        self.NombreSaisons = None
        self.ParentId = None
        self.Pays = None
        self.SaisonsDisponibles = None
        self.Titre = None
        self.TitreIndex = None
        self.Url = None

class SearchResults():
    def __init__(self):
        self.ModifiedQuery = None
        self.Results = None

class SearchResultData():
    def __init__(self):
        self.Emission = None
        self.Episode = None

class Cache():
    def __init__(self):
        pass

    def has_key(self, key):
        pass

    def get(self, key):
        pass

    def set(self, key, value):
        pass

class CacheShelve(Cache):
    def __init__(self):
        self.shelve = shelve.open(".toutv_cache")

    def has_key(self, key):
        return self.shelve.has_key(key)

    def get(self, key):
        return self.shelve[key]

    def set(self, key, value):
        self.shelve[key] = value

    def __del__(self):
        self.shelve.close()

class Transport():
    def __init__(self):
        pass

    def get_emissions(self):
        pass

    def get_episodes_for_emission(self, emission_id):
        pass

    def get_page_repertoire(self):
        pass

class TransportSoap():
    """
        GetArborescence()
        GetBlocPromo()
        GetBlocPromoItems()
        GetCarrousel(xs:string playlistName, )
        GetCollections()
        GetConfiguration()
        GetEmissions()
        GetEmissionsContenusCourts()
        GetEmissionsExclusiviteRogers()
        GetEpisodesExclusiviteRogers()
        GetEpisodesForEmission(xs:long emissionId, )
        GetGenres()
        GetOldestEpisode(xs:long emissionId, )
        GetPageAccueil()
        GetPageEmission(xs:long emissionId, )
        GetPageEpisode(xs:long episodeId, )
        GetPageGenre(xs:string genre, )
        GetPageRepertoire()
        GetPartenaires()
        GetPays()
        GetTeaser(xs:long emissionId, )
        SearchTerms(xs:string query, )
        SearchTermsMax(xs:string query, xs:int maximumNumberOfResults, )
    """
    def __init__(self):
        self.soap = suds.client.Client(TOUTV_WSDL_URL)
        self.soap.set_options(headers={"User-Agent" : IPHONE4_USER_AGENT})

        self.mapper = MapperSoap()

    def get_emissions(self):
        emissions_dto = self.soap.service.GetEmissions()
        emissions = {}

        for emission_dto in emissions_dto[0]:
            emission = self.mapper.dto_to_bo(emission_dto, "Emission")
            emissions[emission.Id] = emission

        return emissions

    def get_episodes_for_emission(self, emission_id):
        episodes_dto = self.soap.service.GetEpisodesForEmission(emission_id)
        episodes = {}

        if len(episodes_dto) > 0:
            for episode_dto in episodes_dto[0]:
                episode = self.mapper.dto_to_bo(episode_dto, "Episode")
                episodes[episode.Id] = episode

        return episodes

    def get_page_repertoire(self):
        repertoire = {}
        repertoire_dto = self.soap.service.GetPageRepertoire()

        if len(repertoire_dto) > 0:
            # EmissionRepertoire
            if len(repertoire_dto[0]) > 0:
                emissionrepertoires = {}
                for emissionrepertoire_dto in repertoire_dto[0][0]:
                    emissionrepertoire = self.mapper.dto_to_bo(emissionrepertoire_dto, "EmissionRepertoire")
                    emissionrepertoires[emissionrepertoire.Id] = emissionrepertoire
                repertoire["emissionrepertoire"] = emissionrepertoires
            # Genre
            if len(repertoire_dto[1]) > 0:
                pass

        return repertoire

    def search_terms(self, query):
        searchresults_dto = self.soap.service.SearchTerms(query)
        searchresults = None
        searchresultdatas = []

        if len(searchresults_dto) > 0:
            searchresults = self.mapper.dto_to_bo(searchresults_dto, "SearchResults")
            if searchresults.Results is not None:
                for searchresultdata_dto in searchresults.Results[0]:
                    searchresultdatas.append(self.mapper.dto_to_bo(searchresultdata_dto, "SearchResultData"))

            searchresults.Results = searchresultdatas

        return searchresults

class ToutvClient():
    def __init__(self, transport=None, cache=None):
        self.transport = transport
        self.cache = cache

    def get_emissions(self, use_cache=True):
        emissions = {}

        if use_cache:
            if not self.cache.has_key('emissions'):
                # Init cache
                self.cache.set('emissions', self.transport.get_emissions())
            emissions = self.cache.get('emissions')
        else:
            emissions = self.transport.get_emissions()
            # Refresh cache
            self.cache.set('emissions', emissions)

        return emissions

    """
    TODO - Implement use_cache flag
    """
    def get_episodes_for_emission(self, emission_id, use_cache=True):
        episodes_per_emission = {}

        if not self.cache.has_key('episodes'):
            self.cache.set('episodes', episodes_per_emission)

        episodes_per_emission = self.cache.get('episodes')

        if not (emission_id in episodes_per_emission):
            episodes_per_emission[emission_id] = self.transport.get_episodes_for_emission(emission_id)
            self.cache.set('episodes', episodes_per_emission)

        return episodes_per_emission[emission_id]

    def fetch_playlist_url(self, episode_pid):
        req = urllib2.Request(TOUTV_PLAYLIST_URL % episode_pid, None, {"User-Agent" : IPHONE4_USER_AGENT})

        response = json.load(urllib2.urlopen(req))

        return response['url']

    """
    TODO - Implement use_cache flag
    """
    def get_page_repertoire(self, use_cache=True):
        repertoire = {}

        if not self.cache.has_key('repertoire'):
            self.cache.set('repertoire', repertoire)

        repertoire = self.cache.get('repertoire')

        if not ("emissionrepertoire" in repertoire):
            repertoire = self.transport.get_page_repertoire()
            self.cache.set('repertoire', repertoire)

        return repertoire

    def search_terms(self, query):
        return self.transport.search_terms(query)

    def search_terms_max(self, query, max_results):
        pass

class ToutvConsoleApp():
    def __init__(self):
        self.argparse = self.build_argparser()
        self.toutvclient = self.build_toutvclient()

    def run(self):
        args = self.argparse.parse_args()
        args.func(args)

    def build_argparser(self):
        parser = argparse.ArgumentParser(description='Tou.tv console script')

        subparsers = parser.add_subparsers(dest="command", help='Sub-commands help')

        # list command
        parser_list = subparsers.add_parser('list', help='List emissions or episodes of an emission')
        parser_list.add_argument('emission', action="store", nargs="?", default=0, type=int, help='List all episodes of an emission')
        parser_list.add_argument('-a', '--all', action="store_true", help='List emissions without any episodes listed')
        parser_list.set_defaults(func=self.command_list)

        # info command
        parser_info = subparsers.add_parser('info', help='Get information about an emission or episode')
        parser_info.add_argument('emission', action="store", nargs=1, type=int, help='Get information about an emission')
        parser_info.add_argument('episode', action="store", nargs="?", default=0, type=int, help='Get information about an episode')
        parser_info.set_defaults(func=self.command_info)

        # fetch command
        parser_fetch = subparsers.add_parser('fetch', help='Fetch one or all episodes of an emission')
        parser_fetch.add_argument('emission', action="store", nargs=1, type=int, help='Fetch all episodes of the provided emission')
        parser_fetch.add_argument('episode', action="store", nargs="?", type=int, help='Fetch the episode')
        parser_fetch.add_argument('-b', '--bitrate', action="store", nargs=1, default="AVERAGE", choices=["MIN", "AVERAGE", "MAX"], help='Specify the bitrate (default: AVERAGE)')
        parser_fetch.add_argument('-d', '--directory', action="store", nargs=1, default=os.getcwd(), help='Output directory (default: ' + os.getcwd() + '/<file>)')
        parser_fetch.set_defaults(func=self.command_fetch)

        # search command
        parser_search = subparsers.add_parser('search', help='Search into toutv emission and episodes')
        parser_search.add_argument('query', action="store", nargs=1, type=str, help='Search query')
        parser_search.add_argument('-m', '--max', action="store", nargs=1, default=0, type=int, help='Maximum number of results (default: infinite)')
        parser_search.set_defaults(func=self.command_search)

        return parser

    def build_toutvclient(self):
        transport = TransportSoap()
        cache = CacheShelve()

        toutvclient = ToutvClient(transport, cache)

        return toutvclient

    def command_list(self, args):
        if args.emission > 0:
            self.list_episodes(args.emission)
        else:
            self.list_emissions(args.all)

    def command_info(self, args):
        if args.episode > 0:
            self.info_episode(args.emission[0], args.episode)
        else:
            self.info_emission(args.emission[0])

    def command_fetch(self, args):
        self.fetch_episodes(args.emission[0], args.episode, args.directory, args.bitrate[0])

    def command_search(self, args):
        self.search(' '.join(args.query))

    def search(self, query):
        searchresult = self.toutvclient.search_terms(query)

        print("Query:")
        if searchresult.ModifiedQuery != query:
            print("\t" + searchresult.ModifiedQuery + " (" + query + ")")
        else:
            print("\t" + searchresult.ModifiedQuery)

        print("Results:")
        if len(searchresult.Results) == 0:
                print("\tNo result found for " + query)
        else:
            for result in searchresult.Results:
                if result.Emission is not None:
                    print("\tEmission:")
                    print("\t\t" + result.Emission.Title)
                    if result.Emission.Description:
                        description = textwrap.wrap(result.Emission.Description, 100)
                        for line in description:
                            print("\t\t\t" + line)
                if result.Episode is not None:
                    print("\tEpisode:")
                    print("\t\t" + result.Episode.Title)
                    if result.Episode.Description:
                        description = textwrap.wrap(result.Episode.Description, 100)
                        for line in description:
                            print("\t\t\t" + line)

    def list_emissions(self, all=False):
        if all:
            emissions = self.toutvclient.get_emissions()
            for e in emissions:
                print(e.Title + " - " + str(e.Id))
        else:
            repertoire = self.toutvclient.get_page_repertoire()
            emissionrepertoires = repertoire["emissionrepertoire"]

            for k in emissionrepertoires:
                print(emissionrepertoires[k].Titre + " - " + str(emissionrepertoires[k].Id))

    def list_episodes(self, emission_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        print("Title:")
        print("\t" + emission.Title)

        print("Episodes:")
        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

        if len(episodes) == 0:
            print("\tNo episodes for the provided emission ("+emission.Title+")")
        else:
            for k in episodes:
                print("\t" + str(episodes[k].Id) + " - " + episodes[k].Title)

    def info_emission(self, emission_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        print("Title: ")
        print("\t" + emission.Title + "\t(" + (emission.Country if emission.Country else "Pays inconnu") + (" - " + str(emission.Year) if emission.Year else "") + ")")

        print("Description:")
        if emission.Description:
            description = textwrap.wrap(emission.Description, 100)
            for line in description:
                print("\t" + line)
        else:
            print("\tAucune description")

        print("Network:")
        if emission.Network:
            print("\t" + emission.Network)
        else:
            print("\tunknown")

        print("Will be removed:")
        if emission.DateRetraitOuEmbargo:
            if emission.DateRetraitOuEmbargo == "":
                print("\t" + str(emission.DateRetraitOuEmbargo))
            else:
                print("\tnot available")
        else:
            print("\tunknown")

        print "Tags: ",
        if emission.EstContenuJeunesse:
            print "jeune ",
        if emission.EstExclusiviteRogers:
            print "rogers "

    def info_episode(self, emission_id, episode_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)
        if len(episodes) == 0:
            print("No episodes")
            sys.exit(1)

        episode = episodes[episode_id]

        print("Emission:")
        print("\t" + emission.Title)

        print("Title:")
        print("\t" + episode.Title + "\t(" + episode.SeasonAndEpisode + ")")

        print("Date aired:")
        print("\t" + episode.AirDateFormated)

        print("Description")
        if episode.Description:
            description = textwrap.wrap(episode.Description, 100)
            for line in description:
                print("\t" + line)
        else:
            print("No description")

        print("Available bandwidth:")

    def fetch_episodes(self, emission_id, episode_id, directory, bitrate="AVERAGE"):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)
        if len(episodes) == 0:
            print("No episodes for <" + emission.Title + ">")
            sys.exit(1)

        episode = episodes[episode_id]

        print("Emission and episode:")
        print("\t" + emission.Title + " - " + episode.Title + "\t(" + episode.SeasonAndEpisode + ")")

        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())))

        url = self.toutvclient.fetch_playlist_url(episode.PID)
        request = urllib2.Request(url, None, {"User-Agent" : IPHONE4_USER_AGENT})
        m3u8_file = urllib2.urlopen(request).read()

        m3u8_parser = M3u8_Parser()

        playlist = m3u8_parser.parse(m3u8_file, os.path.dirname(url))

        stream = self.get_video_stream_bandwidth(playlist, bitrate)

        request = urllib2.Request(stream.uri, None, {'User-Agent': IPHONE4_USER_AGENT} )
        m3u8_file = urllib2.urlopen(request).read()

        playlist = m3u8_parser.parse(m3u8_file, os.path.dirname(stream.uri))

        request = urllib2.Request(playlist.segments[0].key.uri, None, {'User-Agent':IPHONE4_USER_AGENT})
        key = urllib2.urlopen(request).read()

        # Output file handling
        if directory is None:
            directory = os.getcwd()

        if not os.path.exists(os.path.expanduser(directory)):
            os.mkdir(os.path.expanduser(directory))

        sys.stdout.write("Downloading " + str(len(playlist.segments)) + " segments...\n")
        sys.stdout.flush()
        progressbar = ProgressBar(0, len(playlist.segments), mode='fixed')
        output_file = open(os.path.join(os.path.expanduser(directory), emission.Title + "-" + episode.Title + ".ts"), "w")
        count = 1
        for segment in playlist.segments:
            request = urllib2.Request(segment.uri, None, {'User-Agent' : IPHONE4_USER_AGENT})
            ts_file = urllib2.urlopen(request).read()

            aes = AES.new(key, AES.MODE_CBC, struct.pack(">IIII", 0x0, 0x0, 0x0, count))

            output_file.write(aes.decrypt(ts_file))

            count += 1

            progressbar.increment_amount()
            print progressbar, '\r',
            sys.stdout.flush()

        sys.stdout.write("\n")
        sys.stdout.flush()

        output_file.close()

        return None

    """
    They dont' use the "AUDIO" or "VIDEO" m3u8 tag so we must parse the URL
    index_X_av.m3u8 -> audio-video (av)
    index_X_a.m3u8 -> audio (a)
    """
    def get_video_stream_bandwidth(self, playlist, bitrate_type):
        bitrates = []
        for stream in playlist.streams:
            index = os.path.basename(stream.uri)
            if index.split("_", 2)[2][0:2] == "av":
                bitrates.append(stream.bandwidth)

        if bitrate_type == "MIN":
            bandwidth = min(bitrates, key=int)
        elif bitrate_type == "MAX":
            bandwidth = max(bitrates, key=int)
        else:
            # AVERAGE
            bandwidth =  bitrates[((len(bitrates)+1)/2 if len(bitrates)%2 else len(bitrates)/2)]

        for stream in playlist.streams:
            if stream.bandwidth == bandwidth:
                return stream

#
# _/~MAIN~\_
#
if __name__ == "__main__":
    app = ToutvConsoleApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("quitting...")

    sys.exit(0)
