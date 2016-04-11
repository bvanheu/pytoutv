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

import toutv3


# Base model object.
class _Base:
    def __init__(self, agent):
        self._agent = agent

    def _set_agent(self, agent):
        self._agent = agent

    def __getstate__(self):
        # we do not want the agent to be serialized because this is
        # useless: we're going to replace it with the effective agent
        # once loaded anyway
        props = self.__dict__.copy()
        del props['_agent']

        return props


# A key, used to uniquely represent a show, an episode, etc.
class Key(_Base):
    """
    Show/episode's unique key.

    Key objects are comparable.
    """

    def __init__(self, agent, key):
        super().__init__(agent)
        self._key = key

    def __eq__(self, other):
        if type(self) is not type(other):
            return False

        return self.key == other.key

    @property
    def key(self):
        """
        Key's string.
        """

        return self._key

    @property
    def key_type(self):
        """
        Key's type (string).
        """

        return self._key.split('-')[0]

    @property
    def key_code(self):
        """
        Key's code (string).
        """

        return self._key.split('-')[1]

    def __str__(self):
        return self._key


# A user bookmark.
class Bookmark(_Base):
    """
    TOU.TV user bookmark.
    """

    def __init__(self, agent, key, creation_date):
        super().__init__(agent)
        self._key = key
        self._creation_date = creation_date

    def _set_agent(self, agent):
        super()._set_agent(agent)
        self._key._set_agent(agent)

    @property
    def show(self):
        """
        :py:class:`Show` object which corresponds to this bookmark,
        or ``None`` if it cannot be found.
        """

        for search_show_summary in self._agent.get_search_show_summaries():
            if search_show_summary.key == self.key:
                return search_show_summary.show

    @property
    def key(self):
        """
        Bookmark's unique key (:py:class:`Key` object).
        """

        return self._key

    @property
    def creation_date(self):
        """
        Creation date of this bookmark (:py:class:`datetime.datetime`).
        """

        return self._creation_date


# User informations.
#
# is_hd and is_premium are usually both false or both true, and they
# indicate if the user has access to resp. HD bitrates and premium
# content.
#
# rc_telco and rc_features, for premium accounts, indicate if the
# account is premium because the user is a specific telephone company
# client (RC has deals with telephone companies), and the features that
# this deal offers (just another format for the HD/premium flags).
#
# show_ads tells the app whether or not it should display ads.
class UserInfos(_Base):
    """
    TOU.TV user informations and profile.
    """

    def __init__(self, agent, ban_level, name, email, is_hd, bookmarks,
                 stats_metas, rc_telco, rc_features, is_premium, show_ads):
        super().__init__(agent)
        self._ban_level = ban_level
        self._name = name
        self._email = email
        self._is_hd = is_hd
        self._bookmarks = bookmarks
        self._stats_metas = stats_metas
        self._rc_telco = rc_telco
        self._rc_features = rc_features
        self._is_premium = is_premium
        self._show_ads = show_ads

    def _set_agent(self, agent):
        super()._set_agent(agent)

        for bookmark in self._bookmarks:
            bookmark._set_agent(agent)

    @property
    def ban_level(self):
        """
        Ban level of this user or ``None``.
        """

        return self._ban_level

    @property
    def name(self):
        """
        User's full name.
        """

        return self._name

    @property
    def email(self):
        """
        User's email address.
        """

        return self._email

    @property
    def is_hd(self):
        """
        ``True`` if this user can access HD content.
        """

        return self._is_hd

    @property
    def bookmarks(self):
        """
        List of :py:class:`Bookmark` objects of this user.
        """

        return self._bookmarks

    @property
    def stats_metas(self):
        """
        Raw stats metas from the TOU.TV API (:py:class:`dict`).
        """

        return self._stats_metas

    @property
    def rc_telco(self):
        """
        Telephone company of this user, if the user's account is
        associated with one.
        """

        return self._rc_telco

    @property
    def rc_features(self):
        """
        Features of this account enabled by the partnership between
        TOU.TV and the user's telephone company.
        """

        return self._rc_features

    @property
    def is_premium(self):
        """
        ``True`` if this user is a premium user.
        """

        return self._is_premium

    @property
    def show_ads(self):
        """
        ``True`` if this user should see ads.
        """

        return self._show_ads


# A summary of a section.
#
# This is just an association between a section name and its title.
# Sections on TOU.TV are the top containers of shows, like "À la une",
# "Rattrapage télé", "Extra", "Jeunesse", etc.
class SectionSummary(_Base):
    """
    Summary of a section.
    """

    def __init__(self, agent, name, title):
        super().__init__(agent)
        self._name = name
        self._title = title

    @property
    def section(self):
        """
        :py:class:`Section` object which corresponds to this
        section summary.
        """

        return self._agent.get_section(self.name)

    @property
    def name(self):
        """
        Section's name.
        """

        return self._name

    @property
    def title(self):
        """
        Section's title.
        """

        return self._title


# A summary of a show for search purposes.
#
# The app usually has all the available show summaries in one single
# API request. They are kept by the app to make user search queries
# faster: when the user starts typing in the search box, the show
# summaries are searched into using their searchable_text property.
# The suggestion titles use the title property.
#
# is_free indicates whether or not a user must have the premium flag
# to watch the given show.
#
# url is the link, relative to the TOU.TV domain name, to access the
# show page.
class SearchShowSummary(_Base):
    """
    Search show summary.

    This contains the minimum information about a show to search for
    it in a list of such summaries.
    """
    def __init__(self, agent, is_free, image_url, key, searchable_text,
                 url, is_media, is_geolocalized, title):
        super().__init__(agent)
        self._is_free = is_free
        self._image_url = image_url
        self._key = key
        self._searchable_text = searchable_text
        self._url = url
        self._is_media = is_media
        self._is_geolocalized = is_geolocalized
        self._title = title

    def _set_agent(self, agent):
        super()._set_agent(agent)
        self._key._set_agent(agent)

    @property
    def show(self):
        """
        :py:class:`Show` object which corresponds to this
        search show summary.
        """

        return self._agent.get_show(self.url)

    @property
    def is_free(self):
        """
        ``True`` if this show is available to non-premium users.
        """

        return self._is_free

    @property
    def image_url(self):
        """
        URL of the static image file of this show.
        """

        return self._image_url

    @property
    def key(self):
        """
        Show's unique key (:py:class:`Key` object).
        """

        return self._key

    @property
    def searchable_text(self):
        """
        Text in which a user's search term should be searched instead
        of using the title.
        """

        return self._searchable_text

    @property
    def url(self):
        """
        Show's URL name.
        """

        return self._url

    @property
    def is_media(self):
        """
        ``True`` if this show has no seasons/episodes.
        """

        return self._is_media

    @property
    def is_geolocalized(self):
        """
        ``True`` if this show is geolocalized.
        """

        return self._is_geolocalized

    @property
    def title(self):
        """
        Show's title.
        """

        return self._title

    def __repr__(self):
        fmt = "SearchShowSummary(title='{s.title}', key='{s.key}', url='{s.url}')"
        return fmt.format(s=self)


# A show lineup item.
class ShowLineupItem(_Base):
    """
    Show lineup item: an item in the :py:attr:`SubsectionLineup.items`
    list.
    """

    def __init__(self, agent, key, description, image_url, is_active, is_drm,
                 is_free, is_geolocalized, length_text, share_url, template,
                 title, url):
        super().__init__(agent)
        self._key = key
        self._description = description
        self._image_url = image_url
        self._is_active = is_active
        self._is_drm = is_drm
        self._is_free = is_free
        self._is_geolocalized = is_geolocalized
        self._length_text = length_text
        self._share_url = share_url
        self._template = template
        self._title = title
        self._url = url

    def _set_agent(self, agent):
        super()._set_agent(agent)
        self._key._set_agent(agent)

    @property
    def show(self):
        """
        :py:class:`Show` object which corresponds to this
        show lineup item.
        """

        return self._agent.get_show(self.url)

    @property
    def key(self):
        """
        Show's unique key (:py:class:`Key` object).
        """

        return self._key

    @property
    def description(self):
        """
        Show's textual description.
        """

        return self._description

    @property
    def image_url(self):
        """
        URL of the static image file of this show.
        """

        return self._image_url

    @property
    def is_active(self):
        """
        ``True`` if this show is active.
        """

        return self._is_active

    @property
    def is_drm(self):
        """
        ``True`` if this show is protected by DRM.
        """

        return self._is_drm

    @property
    def is_free(self):
        """
        ``True`` if this show is available to non-premium users.
        """

        return self._is_free

    @property
    def is_geolocalized(self):
        """
        ``True`` if this show is geolocalized.
        """

        return self._is_geolocalized

    @property
    def length_text(self):
        """
        Textual length information of this show.
        """

        return self._length_text

    @property
    def share_url(self):
        """
        Full sharing URL of this show.
        """

        return self._share_url

    @property
    def template(self):
        return self._template

    @property
    def title(self):
        """
        Show's title.
        """

        return self._title

    @property
    def url(self):
        """
        Show's URL name.
        """

        return self._url


# A subsection lineup.
class SubsectionLineup(_Base):
    """
    Subsection lineup: a lineup in the :py:attr:`Section.subsection_lineups`
    list.
    """

    def __init__(self, agent, name, title, is_free, items):
        super().__init__(agent)
        self._name = name
        self._title = title
        self._is_free = is_free
        self._items = items

    def _set_agent(self, agent):
        super()._set_agent(agent)

        for item in self._items:
            item._set_agent(agent)

    @property
    def name(self):
        """
        Subsection's name.
        """

        return self._name

    @property
    def title(self):
        """
        Subsection's title.
        """

        return self._title

    @property
    def is_free(self):
        """
        ``True`` if this subsection is available to non-premium users.
        """

        return self._is_free

    @property
    def items(self):
        """
        A list of :py:class:`ShowLineupItem` objects.
        """

        return self._items


# A section.
class Section(_Base):
    """
    TOU.TV section.
    """

    def __init__(self, agent, name, title, subsection_lineups, stats_metas):
        super().__init__(agent)
        self._name = name
        self._title = title
        self._subsection_lineups = subsection_lineups
        self._stats_metas = stats_metas

    def _set_agent(self, agent):
        super()._set_agent(agent)

        for subsection_lineup in self._subsection_lineups:
            subsection_lineup._set_agent(agent)

    @property
    def name(self):
        """
        Section's name.
        """

        return self._name

    @property
    def title(self):
        """
        Section's title.
        """

        return self._title

    @property
    def subsection_lineups(self):
        """
        A list of :py:class:`SubsectionLineup` objects.
        """

        return self._subsection_lineups

    @property
    def stats_metas(self):
        """
        Raw stats metas from the TOU.TV API (:py:class:`dict`).
        """

        return self._stats_metas


# A network.
class Network(_Base):
    """
    A broadcast network.
    """

    def __init__(self, agent, name, image_url, url, title):
        super().__init__(agent)
        self._name = name
        self._image_url = image_url
        self._url = url
        self._title = title

    @property
    def name(self):
        """
        Network's name.
        """

        return self._name

    @property
    def image_url(self):
        """
        URL of the static image file of this network.
        """

        return self._image_url

    @property
    def url(self):
        """
        Network's URL.
        """

        return self._url

    @property
    def title(self):
        """
        Network's title.
        """

        return self._title


# Some credits.
class Credits(_Base):
    """
    Credits.
    """

    def __init__(self, agent, role, names):
        super().__init__(agent)
        self._role = role
        self._names = names

    @property
    def role(self):
        """
        Role of the persons to which those credits are attributed.
        """

        return self._role

    @property
    def names(self):
        """
        Names of the persons to which those credits are attributed
        (string).
        """

        return self._names


# The details of an item (show or episode).
class Details(_Base):
    """
    Details about a :py:class:`Show` or an
    :py:class:`EpisodeLineupItem` object.
    """

    def __init__(self, agent, rating, air_date_text, original_title, credits,
                 copyright, description, country, length_text,
                 length, production_year, details_type,
                 image_url, networks):
        super().__init__(agent)
        self._rating = rating
        self._air_date_text = air_date_text
        self._original_title = original_title
        self._credits = credits
        self._copyright = copyright
        self._description = description
        self._country = country
        self._length_text = length_text
        self._length = length
        self._production_year = production_year
        self._details_type = details_type
        self._image_url = image_url
        self._networks = networks

    def _set_agent(self, agent):
        super()._set_agent(agent)

        for credit in self._credits:
            credit._set_agent(agent)

        for network in self._networks:
            network._set_agent(agent)

    @property
    def rating(self):
        """
        Program rating (string).
        """

        return self._rating

    @property
    def air_date_text(self):
        """
        Textual air date.
        """

        return self._air_date_text

    @property
    def original_title(self):
        """
        Original title.
        """

        return self._original_title

    @property
    def credits(self):
        """
        A list of :py:class:`Credits` objects.
        """

        return self._credits

    @property
    def copyright(self):
        """
        Copyright notice.
        """

        return self._copyright

    @property
    def description(self):
        """
        Description.
        """

        return self._description

    @property
    def country(self):
        """
        Country of origin.
        """

        return self._country

    @property
    def length_text(self):
        """
        Textual length information.
        """

        return self._length_text

    @property
    def length(self):
        """
        Length in seconds (integer).
        """

        return self._length

    @property
    def production_year(self):
        """
        Production year.
        """

        return self._production_year

    @property
    def details_type(self):
        return self._details_type

    @property
    def image_url(self):
        """
        URL of the static image file of this show/episode.
        """

        return self._image_url

    @property
    def networks(self):
        """
        List of :py:class:`Network` objects.
        """

        return self._networks


# A show.
class Show(_Base):
    """
    TOU.TV show.
    """

    def __init__(self, agent, key, description, bg_image_url, image_url, title,
                 details, id_media, season_lineups, stats_metas):
        super().__init__(agent)
        self._key = key
        self._description = description
        self._bg_image_url = bg_image_url
        self._image_url = image_url
        self._title = title
        self._details = details
        self._season_lineups = season_lineups
        self._stats_metas = stats_metas
        self._id_media = id_media

    def _set_agent(self, agent):
        super()._set_agent(agent)
        self._key._set_agent(agent)
        self._details._set_agent(agent)

        for season_lineup in self._season_lineups:
            season_lineup._set_agent(agent)

    @property
    def key(self):
        """
        Show's unique key (:py:class:`Key` object).
        """

        return self._key

    @property
    def description(self):
        """
        Show's description.
        """

        return self._description

    @property
    def bg_image_url(self):
        """
        URL of the static background image file of this show.
        """

        return self._bg_image_url

    @property
    def image_url(self):
        """
        URL of the static image file of this show.
        """

        return self._image_url

    @property
    def title(self):
        """
        Show's title.
        """

        return self._title

    @property
    def details(self):
        """
        Show's details (:py:class:`Details` object).
        """

        return self._details

    @property
    def season_lineups(self):
        """
        List of :py:class:`SeasonLineup` objects.
        """

        return self._season_lineups

    @property
    def stats_metas(self):
        """
        Raw stats metas from the TOU.TV API (:py:class:`dict`).
        """

        return self._stats_metas

    @property
    def id_media(self):
        return self._id_media


# A season lineup.
class SeasonLineup(_Base):
    """
    Season lineup: a lineup in the :py:attr:`Show.season_lineups`
    list.
    """

    def __init__(self, agent, name, title, url, is_free, items):
        super().__init__(agent)
        self._name = name
        self._title = title
        self._url = url
        self._is_free = is_free
        self._items = items

    def _set_agent(self, agent):
        super()._set_agent(agent)

        for item in self._items:
            item._set_agent(agent)

    @property
    def name(self):
        """
        Season's name.
        """

        return self._name

    @property
    def title(self):
        """
        Season's title.
        """

        return self._title

    @property
    def url(self):
        """
        Season's URL name.
        """

        return self._url

    @property
    def is_free(self):
        """
        ``True`` if this season is available to non-premium users.
        """

        return self._is_free

    @property
    def items(self):
        """
        List of :py:class:`EpisodeLineupItem` objects.
        """

        return self._items


# An episode lineup item.
class EpisodeLineupItem(_Base):
    """
    Episode lineup item: an item in the :py:attr:`SeasonLineup.items`
    list.
    """

    def __init__(self, agent, template, is_active, url, is_free, key,
                 is_geolocalized, image_url, title, is_drm, description,
                 share_url, details):
        super().__init__(agent)
        self._template = template
        self._is_active = is_active
        self._url = url
        self._is_free = is_free
        self._key = key
        self._is_geolocalized = is_geolocalized
        self._image_url = image_url
        self._title = title
        self._is_drm = is_drm
        self._description = description
        self._share_url = share_url
        self._details = details
        self._id_media = None

    def _set_agent(self, agent):
        super()._set_agent(agent)
        self._key._set_agent(agent)
        self._details._set_agent(agent)

    @property
    def template(self):
        return self._template

    @property
    def is_active(self):
        """
        ``True`` if this episode is active.
        """

        return self._is_active

    @property
    def url(self):
        """
        Episode's URL name.
        """

        return self._url

    @property
    def is_free(self):
        """
        ``True`` if this episode is available to non-premium users.
        """

        return self._is_free

    @property
    def key(self):
        """
        Episode's unique key (:py:class:`Key` object).
        """

        return self._key

    @property
    def is_geolocalized(self):
        """
        ``True`` if this episode is geolocalized.
        """

        return self._is_geolocalized

    @property
    def image_url(self):
        """
        URL of the static image file of this episode.
        """

        return self._image_url

    @property
    def title(self):
        """
        Episode's title.
        """

        return self._title

    @property
    def is_drm(self):
        """
        ``True`` if this episode is protected by DRM.
        """

        return self._is_drm

    @property
    def description(self):
        """
        Episode's description.
        """

        return self._description

    @property
    def share_url(self):
        """
        Full sharing URL of this episode.
        """

        return self._share_url

    @property
    def details(self):
        """
        Episode's details (:py:class:`Details` object).
        """

        return self._details

    @property
    def id_media(self):
        if not self._id_media:
            if not self._url:
                return

            show = self._agent.get_show(self._url)

            if show.id_media is None:
                raise toutv3.ApiChanged()

            self._id_media = show.id_media

        return self._id_media

    @property
    def media_versions(self):
        """
        List of :py:class:`MediaVersion` objects.
        """

        return self._agent.get_media_versions(self.id_media)


# A media version. This is what you have to get for creating a
# download of this specific version.
class MediaVersion(_Base):
    """
    Media version of a show or of an episode.
    """

    def __init__(self, agent, id_media, variant_stream):
        super().__init__(agent)
        self._id_media = id_media
        self._variant_stream = variant_stream

    @property
    def id_media(self):
        return self._id_media

    @property
    def bandwidth(self):
        """
        Bandwidth, in bps.
        """

        return self._variant_stream.bandwidth

    @property
    def resolution(self):
        """
        Resolution tuple (width, height), or ``None`` if the resolution
        is not available.
        """

        if self._variant_stream.resolution:
            reso = self._variant_stream.resolution

            return (reso.width, reso.height)

    def create_download(self):
        """
        Creates a :py:class:`toutv3.download.Download` object ready
        to download this media version.
        """

        return self._agent.get_download(self._variant_stream)
