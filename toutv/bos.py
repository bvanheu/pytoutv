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


import datetime
import logging
import os
import re
import requests
import toutv.dl
import toutv.config
import toutv.m3u8


def _clean_description(desc):
    desc = desc.replace('\n', ' ')
    desc = desc.replace('  ', ' ')

    return desc.strip()


class _Bo:

    def set_auth(self, auth):
        self._auth = auth

    def get_auth(self):
        if hasattr(self, '_auth'):
            return self._auth

        self._auth = None

        return self._auth

    def set_proxies(self, proxies):
        self._proxies = proxies

    def get_proxies(self):
        if hasattr(self, '_proxies'):
            return self._proxies

        self._proxies = None

        return self._proxies

    def _do_request(self, url, timeout=None, params=None):
        proxies = self.get_proxies()
        auth = self.get_auth()

        try:
            headers = dict(toutv.config.HEADERS)

            if auth and params:
                url = toutv.config.TOUTV_AUTH_PLAYLIST_URL
                token = auth.get_token()
                params['claims'] = auth.get_claims(token)
                headers['Authorization'] = "Bearer " + token
                headers['Host'] = "services.radio-canada.ca"

            r = requests.get(url, params=params, headers=headers,
                             proxies=proxies, timeout=timeout)
            if r.status_code != 200:
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url,
                                                                     r.status_code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, timeout)

        return r


class _ThumbnailProvider:

    def _cache_medium_thumb(self):
        if self.has_medium_thumb_data():
            # No need to download again
            return

        urls = self.get_medium_thumb_urls()

        for url in urls:
            if not url:
                continue

            logging.debug('HTTP-getting "{}"'.format(url))

            try:
                r = self._do_request(url, timeout=2)
            except Exception as e:
                # Ignore any network error
                logging.warning(e)
                continue

            self._medium_thumb_data = r.content
            break

    def get_medium_thumb_data(self):
        self._cache_medium_thumb()

        return self._medium_thumb_data

    def has_medium_thumb_data(self):
        if not hasattr(self, '_medium_thumb_data'):
            self._medium_thumb_data = None

        return (self._medium_thumb_data is not None)

    def get_medium_thumb_urls(self):
        """Returns a list of possible thumbnail urls in order of preference."""
        raise NotImplementedError()


class _AbstractEmission(_Bo):

    def get_id(self):
        return self.Id

    def get_genre(self):
        return self.Genre

    def get_url(self):
        if self.Url is None:
            return None

        return '{}/{}'.format(toutv.config.TOUTV_BASE_URL, self.Url)

    def get_removal_date(self):
        if self.DateRetraitOuEmbargo is None:
            return None

        # Format looks like: /Date(1395547200000-0400)/
        # Sometimes we have weird values: '/Date(-62135578800000-0500)/',
        # we'll return None in that case.
        d = self.DateRetraitOuEmbargo
        m = re.match(r'/Date\((\d+)-\d+\)/', d)
        if m is not None:
            ts = int(m.group(1)) // 1000

            return datetime.datetime.fromtimestamp(ts)

        return None

    def __str__(self):
        return '{} ({})'.format(self.get_title(), self.get_id())


class Emission(_AbstractEmission, _ThumbnailProvider):

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
        self._episodes = {}

    def add_episode(self, episode):
        self._episodes[episode.Id] = episode

    def get_episodes(self):
        return self._episodes.values()

    def get_title(self):
        return self.Title

    def get_year(self):
        return self.Year

    def get_country(self):
        return self.Country

    def get_description(self):
        if self.Description is None:
            return None
        return _clean_description(self.Description)

    def get_network(self):
        if self.Network == '(not specified)':
            return None

        if self.Network is None:
            # We observed CBFT (SRC) is the default network when not specified
            return 'CBFT'

        return self.Network

    def get_tags(self):
        tags = []
        if self.EstExclusiviteRogers:
            tags.append('rogers')
        if self.EstContenuJeunesse:
            tags.append('youth')

        return tags

    def get_medium_thumb_urls(self):
        name = self.Url.replace('-', '')
        url = toutv.config.EMISSION_THUMB_URL_TMPL.format(name)

        return [url, self.ImagePromoNormalK]


class Genre(_Bo):

    def __init__(self):
        self.CategoryURL = None
        self.ClassCategory = None
        self.Description = None
        self.Id = None
        self.ImageBackground = None
        self.ParentId = None
        self.Title = None
        self.Url = None

    def get_id(self):
        return self.Id

    def get_title(self):
        return self.Title

    def __str__(self):
        return '{} ({})'.format(self.get_title(), self.get_id())


class Episode(_Bo, _ThumbnailProvider):

    class Quality:

        def __init__(self, bitrate, xres, yres):
            self._bitrate = bitrate
            self._xres = xres
            self._yres = yres

        @property
        def bitrate(self):
            return self._bitrate

        @property
        def xres(self):
            return self._xres

        @property
        def yres(self):
            return self._yres

        def __hash__(self):
            return hash(self._bitrate) + hash(self._xres) + hash(self._yres)

        def __eq__(self, other):
            return self.bitrate == other.bitrate and self.xres == other.xres \
                and self.yres == other.yres

        def __repr__(self):
            s = 'Quality(res={xres}x{yres}, bitrate={bitrate})'
            return s.format(xres=self.xres,
                            yres=self.yres,
                            bitrate=self.bitrate)

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
        self._playlist = None
        self._cookies = None

    def get_title(self):
        return self.Title

    def get_id(self):
        return self.Id

    def get_author(self):
        return self.PeopleAuthor

    def get_director(self):
        return self.PeopleDirector

    def get_year(self):
        return self.Year

    def get_genre_title(self):
        return self.GenreTitle

    def get_url(self):
        if self.Url is None:
            return None

        return '{}/{}'.format(toutv.config.TOUTV_BASE_URL, self.Url).replace('tou.tv//', 'tou.tv/')

    def get_season_number(self):
        return self.SeasonNumber

    def get_episode_number(self):
        return self.EpisodeNumber

    def get_sae(self):
        return self.SeasonAndEpisode or 'S00E00'

    def get_description(self):
        if self.Description is None:
            return None
        return _clean_description(self.Description)

    def get_emission_id(self):
        return self.CategoryId

    def get_length(self):
        tot_seconds = int(self.Length) // 1000
        minutes = tot_seconds // 60
        seconds = tot_seconds - (60 * minutes)

        return minutes, seconds

    def get_air_date(self):
        if self.AirDateFormated is None:
            return self.AirDateLongString

        dt = datetime.datetime.strptime(self.AirDateFormated, '%Y%m%d')

        return dt.date()

    def set_emission(self, emission):
        self._emission = emission

    def get_emission(self):
        return self._emission

    @staticmethod
    def _get_video_qualities(playlist):
        qualities = []

        for stream in playlist.streams:
            # TOU.TV team doesnt use the "AUDIO" or "VIDEO" M3U8 tags so
            # we must parse the URL to find out about video stream:
            #   index_X_av.m3u8 -> audio-video (av)
            #   index_X_a.m3u8 -> audio (a)
            if not re.search(r'_av\.m3u8', stream.uri):
                continue

            xres = None
            yres = None

            if stream.resolution is not None:
                m = re.match(r'(\d+)x(\d+)', stream.resolution)

                if m:
                    xres = int(m.group(1))
                    yres = int(m.group(2))

            bw = int(stream.bandwidth)
            quality = Episode.Quality(bw, xres, yres)

            qualities.append(quality)

        return qualities

    def _get_playlist_url(self):
        url = toutv.config.TOUTV_PLAYLIST_URL
        params = dict(toutv.config.TOUTV_PLAYLIST_PARAMS)
        params['idMedia'] = self.PID

        num_tries = 3

        for i in range(num_tries):
            r = self._do_request(url, params=params)
            try:
                response_obj = r.json()
                if response_obj['errorCode']:
                    raise RuntimeError(response_obj['message'])
                return response_obj['url']
            except ValueError as e:
                if i + 1 < num_tries:
                    logging.warning("GetPlaylistURL failed. Will retry...")
                else:
                    raise RuntimeError("Error: GetPlaylistURL failed.") from e

    def get_playlist_cookies(self):
        if not self._playlist or not self._cookies:
            url = self._get_playlist_url()
            r = self._do_request(url)

            # parse M3U8 file
            m3u8_file = r.text
            self._playlist = toutv.m3u8.parse(m3u8_file, os.path.dirname(url))
            self._cookies = r.cookies

        return self._playlist, self._cookies

    def get_available_qualities(self):
        # Get playlist
        playlist, cookies = self.get_playlist_cookies()

        # Get video qualities
        qualities = Episode._get_video_qualities(playlist)

        qualities.sort(key=lambda q: q.bitrate)

        return qualities

    def get_medium_thumb_urls(self):
        return [self.ImageThumbMoyenL]

    def __str__(self):
        return '{} ({})'.format(self.get_title(), self.get_id())


class EmissionRepertoire(_AbstractEmission):

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

    def get_title(self):
        return self.Titre

    def get_country(self):
        return self.Pays

    def get_year(self):
        return self.AnneeProduction


class SearchResults(_Bo):

    def __init__(self):
        self.ModifiedQuery = None
        self.Results = None

    def get_modified_query(self):
        return self.ModifiedQuery

    def get_results(self):
        return self.Results


class SearchResultData(_Bo):

    def __init__(self):
        self.Emission = None
        self.Episode = None

    def get_emission(self):
        return self.Emission

    def get_episode(self):
        return self.Episode


class Repertoire(_Bo):

    def __init__(self):
        self.Emissions = None
        self.Genres = None
        self.Pays = None

    def set_emissions(self, emissions):
        self.Emissions = emissions

    def get_emissions(self):
        return self.Emissions
