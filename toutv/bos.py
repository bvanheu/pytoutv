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

class Emission:
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


class Genre:
    def __init__(self):
        self.CategoryURL = None
        self.ClassCategory = None
        self.Description = None
        self.Id = None
        self.ImageBackground = None
        self.ParentId = None
        self.Title = None
        self.Url = None


class Episode:
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


class EmissionRepertoire:
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


class SearchResults:
    def __init__(self):
        self.ModifiedQuery = None
        self.Results = None


class SearchResultData:
    def __init__(self):
        self.Emission = None
        self.Episode = None
