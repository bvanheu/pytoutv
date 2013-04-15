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

import json
import urllib2
import urllib

IPHONE4_USER_AGENT = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"
TOUTV_WSDL_URL = "http://api.tou.tv/v1/TouTVAPIService.svc?wsdl"
TOUTV_PLAYLIST_URL = "http://api.radio-canada.ca/validationMedia/v1/Validation.html?appCode=thePlatform&deviceType=iphone4&connectionType=wifi&idMedia=%s&output=json"
TOUTV_JSON_URL = "https://api.tou.tv/v1/toutvapiservice.svc/json/"

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

class MapperJson(Mapper):
    def dto_to_bo(self, dto, class_type):
        bo = self.factory(class_type)
        bo_vars = vars(bo)

        for key in bo_vars.keys():
            value = dto[key]

            if isinstance(value, unicode):
                value = value.encode("utf-8")
            elif isinstance(value, dict):
                if value["__type"] == "GenreDTO:#RC.Svc.Web.TouTV":
                    value = self.dto_to_bo(value, "Genre")
                elif value["__type"] in ["EmissionDTO:#RC.Svc.Web.TouTV", "EmissionDTO:RC.Svc.Web.TouTV"]:
                    value = self.dto_to_bo(value, "Emission")
                elif value["__type"] in ["EpisodeDTO:#RC.Svc.Web.TouTV", "EpisodeDTO:RC.Svc.Web.TouTV"]:
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

class Transport():
    def __init__(self):
        pass

    def get_emissions(self):
        pass

    def get_episodes_for_emission(self, emission_id):
        pass

    def get_page_repertoire(self):
        pass

    def search_terms(self, query):
        pass

class TransportJson(Transport):
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
        self.json_decoder = json.JSONDecoder()
        self.mapper = MapperJson()

    def _do_query(self, method, parameters={}):
        parameters_str = urllib.urlencode(parameters)
        url = TOUTV_JSON_URL + method + '?' + parameters_str
        request = urllib2.Request(url, None, {"User-Agent" : IPHONE4_USER_AGENT})
        json_decoded = self.json_decoder.decode(urllib2.urlopen(request).read())
        return json_decoded["d"]

    def get_emissions(self):
        emissions_dto = self._do_query("GetEmissions")

        emissions = {}

        for emission_dto in emissions_dto:
            emission = self.mapper.dto_to_bo(emission_dto, "Emission")
            emissions[emission.Id] = emission

        return emissions

    def get_episodes_for_emission(self, emission_id):
        episodes_dto = self._do_query("GetEpisodesForEmission", {"emissionid": str(emission_id)})

        episodes = {}

        if len(episodes_dto) > 0:
            for episode_dto in episodes_dto:
                episode = self.mapper.dto_to_bo(episode_dto, "Episode")
                episodes[episode.Id] = episode

        return episodes

    def get_page_repertoire(self):
        repertoire_dto = self._do_query("GetPageRepertoire")

        repertoire = {}

        if len(repertoire_dto) > 0:
            # EmissionRepertoire
            if len(repertoire_dto) > 0:
                emissionrepertoires = {}
                for emissionrepertoire_dto in repertoire_dto["Emissions"]:
                    emissionrepertoire = self.mapper.dto_to_bo(emissionrepertoire_dto, "EmissionRepertoire")
                    emissionrepertoires[emissionrepertoire.Id] = emissionrepertoire
                repertoire["emissionrepertoire"] = emissionrepertoires
            # Genre
            if len(repertoire_dto["Genres"]) > 0:
                pass
            # Country
            if len(repertoire_dto["Pays"]) > 0:
                pass

        return repertoire

    def search_terms(self, query):
        searchresults_dto = self._do_query("SearchTerms", {"query": query})
        searchresults = None
        searchresultdatas = []

        if len(searchresults_dto) > 0:
            searchresults = self.mapper.dto_to_bo(searchresults_dto, "SearchResults")
            if searchresults.Results is not None:
                for searchresultdata_dto in searchresults.Results:
                    searchresultdatas.append(self.mapper.dto_to_bo(searchresultdata_dto, "SearchResultData"))

            searchresults.Results = searchresultdatas

        return searchresults

class ToutvClient():
    def __init__(self, transport, cache):
        self.transport = transport
        self.cache = cache

    def get_emissions(self):
        emissions = self.cache.get("emissions")

        if not emissions:
            emissions = self.transport.get_emissions()
            self.cache.set("emissions", emissions)

        return emissions

    def get_episodes_for_emission(self, emission_id):
        episodes_per_emission = self.cache.get("episodes")

        if not episodes_per_emission:
            episodes_per_emission = {}
            episodes_per_emission[emission_id] = self.transport.get_episodes_for_emission(emission_id)
            self.cache.set("episodes", episodes_per_emission)

        if not (emission_id in episodes_per_emission):
            episodes_per_emission[emission_id] = self.transport.get_episodes_for_emission(emission_id)
            self.cache.set("episodes", episodes_per_emission)

        return episodes_per_emission[emission_id]

    def fetch_playlist_url(self, episode_pid):
        req = urllib2.Request(TOUTV_PLAYLIST_URL % episode_pid, None, {"User-Agent" : IPHONE4_USER_AGENT})

        response = json.load(urllib2.urlopen(req))

        if response['errorCode']:
            raise Exception(response['message'])

        return response['url']

    """
    TODO - Implement use_cache flag
    """
    def get_page_repertoire(self, use_cache=True):
        repertoire = self.cache.get("repertoire")

        if not repertoire:
            repertoire = self.transport.get_page_repertoire()
            self.cache.set("repertoire", repertoire)

        return repertoire

    def search_terms(self, query):
        return self.transport.search_terms(query)

    def search_terms_max(self, query, max_results):
        pass
