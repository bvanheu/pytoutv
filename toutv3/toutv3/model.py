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

# A key, used to uniquely represent a show, an episode, etc.
class Key:
    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        return self._key

    @property
    def key_type(self):
        return self._key.split('-')[0]

    @property
    def key_code(self):
        return self._key.split('-')[1]

    def __str__(self):
        return self._key


# A user bookmark.
class Bookmark:
    def __init__(self, key, creation_date):
        self._key = key
        self._creation_date = creation_date

    @property
    def key(self):
        return self._key

    @property
    def creation_date(self):
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
class UserInfos:
    def __init__(self, ban_level, name, email, is_hd, bookmarks,
                 stats_metas, rc_telco, rc_features, is_premium, show_ads):
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

    @property
    def ban_level(self):
        return self._ban_level

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

    @property
    def is_hd(self):
        return self._is_hd

    @property
    def bookmarks(self):
        return self._bookmarks

    @property
    def stats_metas(self):
        return self._stats_metas

    @property
    def rc_telco(self):
        return self._rc_telco

    @property
    def rc_features(self):
        return self._rc_features

    @property
    def is_premium(self):
        return self._is_premium

    @property
    def show_ads(self):
        return self._show_ads


# A summary of a section.
#
# This is just an association between a section ID and its title.
# Sections on TOU.TV are the top containers of shows, like "À la une",
# "Rattrapage télé", "Extra", "Jeunesse", etc.
class SectionSummary:
    def __init__(self, section_id, title):
        self._section_id = section_id
        self._title = title

    @property
    def section_id(self):
        return self._section_id

    @property
    def title(self):
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
class SearchShowSummary:
    def __init__(self, is_free, image_url, key, searchable_text,
                 url, is_media, is_geolocatized, title):
        self._is_free = is_free
        self._image_url = image_url
        self._key = key
        self._searchable_text = searchable_text
        self._url = url
        self._is_media = is_media
        self._is_geolocatized = is_geolocalized
        self._title = title

    @property
    def is_free(self):
        return self._is_free

    @property
    def image_url(self):
        return self._image_url

    @property
    def key(self):
        return self._key

    @property
    def searchable_text(self):
        return self._searchable_text

    @property
    def url(self):
        return self._url

    @property
    def is_media(self):
        return self._is_media

    @property
    def is_geolocalized(self):
        return self._is_geolocalized

    @property
    def title(self):
        return self._title


# A show lineup item.
class ShowLineupItem:
    def __init__(self, key, description, image_url, is_active, is_drm,
                 is_free, is_geolocalized, length_text, share_url, template,
                 title, url):
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

    @property
    def key(self):
        return self._key

    @property
    def description(self):
        return self._description

    @property
    def image_url(self):
        return self._image_url

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_drm(self):
        return self._is_drm

    @property
    def is_free(self):
        return self._is_free

    @property
    def is_geolocalized(self):
        return self._is_geolocalized

    @property
    def length_text(self):
        return self._length_text

    @property
    def share_url(self):
        return self._share_url

    @property
    def template(self):
        return self._template

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url


# A subsection lineup.
class SubsectionLineup:
    def __init__(self, name, title, is_free, items):
        self._name = name
        self._title = title
        self._is_free = is_free
        self._items = items

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def is_free(self):
        return self._is_free

    @property
    def items(self):
        return self._items


# A section.
class Section:
    def __init__(self, name, title, subsection_lineups, stats_metas):
        self._name = name
        self._title = title
        self._subsection_lineups = subsection_lineups
        self._stats_metas = stats_metas

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def subsection_lineups(self):
        return self._subsection_lineups

    @property
    def stats_metas(self):
        return self._stats_metas


# A network.
class Network:
    def __init__(self, name, image_url, url, title):
        self._name = name
        self._image_url = image_url
        self._url = url
        self._title = title

    @property
    def name(self):
        return self._name

    @property
    def image_url(self):
        return self._image_url

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self._title


# Some credits.
class Credits:
    def __init__(self, role, names):
        self._role = role
        self._names = names

    @property
    def role(self):
        return self._role

    @property
    def names(self):
        return self._names


# The details of an item (show or episode).
class Details:
    def __init__(self, rating, air_date_text, original_title, credits,
                 copyright, description, country, length_text,
                 length, production_year, details_type,
                 image_url, networks):
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

    @property
    def rating(self):
        return self._rating

    @property
    def air_date_text(self):
        return self._air_date_text

    @property
    def original_title(self):
        return self._original_title

    @property
    def credits(self):
        return self._credits

    @property
    def copyright(self):
        return self._copyright

    @property
    def description(self):
        return self._description

    @property
    def country(self):
        return self._country

    @property
    def length_text(self):
        return self._length_text

    @property
    def length(self):
        return self._length

    @property
    def production_year(self):
        return self._production_year

    @property
    def details_type(self):
        return self._details_type

    @property
    def image_url(self):
        return self._image_url

    @property
    def networks(self):
        return self._networks


# A show.
class Show:
    def __init__(self, key, description, bg_image_url, image_url, title,
                 details, season_lineups, stats_metas):
        self._key = key
        self._description = description
        self._bg_image_url = bg_image_url
        self._image_url = image_url
        self._title = title
        self._details = details
        self._season_lineups = season_lineups
        self._stats_metas = stats_metas

    @property
    def key(self):
        return self._key

    @property
    def description(self):
        return self._description

    @property
    def bg_image_url(self):
        return self._bg_image_url

    @property
    def image_url(self):
        return self._image_url

    @property
    def title(self):
        return self._title

    @property
    def details(self):
        return self._details

    @property
    def season_lineups(self):
        return self._season_lineups

    @property
    def stats_metas(self):
        return self._stats_metas


# A season lineup.
class SeasonLineup:
    def __init__(self, name, title, url, is_free, items):
        self._name = name
        self._title = title
        self._url = url
        self._is_free = is_free
        self._items = items

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def url(self):
        return self._url

    @property
    def is_free(self):
        return self._is_free

    @property
    def items(self):
        return self._items


# An episode lineup item.
class EpisodeLineupItem:
    def __init__(self, template, is_active, url, is_free, key, is_geolocalized,
                 image_url, title, is_drm, description, share_url, details):
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

    @property
    def template(self):
        return self._template

    @property
    def is_active(self):
        return self._is_active

    @property
    def url(self):
        return self._url

    @property
    def is_free(self):
        return self._is_free

    @property
    def key(self):
        return self._key

    @property
    def is_geolocalized(self):
        return self._is_geolocalized

    @property
    def image_url(self):
        return self._image_url

    @property
    def title(self):
        return self._title

    @property
    def is_drm(self):
        return self._is_drm

    @property
    def description(self):
        return self._description

    @property
    def share_url(self):
        return self._share_url

    @property
    def details(self):
        return self._details
