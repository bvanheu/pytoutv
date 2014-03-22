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
import difflib
import requests
import toutv.cache
import toutv.mapper
import toutv.transport
import toutv.config
import toutv.bos as bos


class NoMatchException(Exception):
    def __init__(self, query, candidates=[]):
        self.query = query
        self.candidates = candidates


class ClientError(RuntimeError):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg


class Client:
    def __init__(self, transport=toutv.transport.JsonTransport(),
                 cache=toutv.cache.EmptyCache()):
        self.transport = transport
        self.cache = cache

    def get_emissions(self):
        emissions = self.cache.get_emissions()
        if emissions is None:
            emissions = self.transport.get_emissions()
            self.cache.set_emissions(emissions)

        return emissions

    def get_emission_episodes(self, emission):
        episodes = self.cache.get_emission_episodes(emission)
        if episodes is None:
            episodes = self.transport.get_emission_episodes(emission)
            self.cache.set_emission_episodes(emission, episodes)

        return episodes

    def get_page_repertoire(self):
        page_repertoire = self.cache.get_page_repertoire()
        if page_repertoire is None:
            page_repertoire = self.transport.get_page_repertoire()
            self.cache.set_page_repertoire(page_repertoire)

        return page_repertoire

    def search(self, query):
        return self.transport.search(query)

    def get_episode_playlist_url(self, episode):
        url = toutv.config.TOUTV_PLAYLIST_URL
        params = dict(toutv.config.TOUTV_PLAYLIST_PARAMS)
        params['idMedia'] = episode.PID

        r = requests.get(url, params=params, headers=toutv.config.headers)
        response_obj = r.json()

        if response_obj['errorCode']:
            raise RuntimeError(response_obj['message'])

        return response_obj['url']

    def get_emission_by_name(self, emission_name):
        emissions = self.get_emissions()
        emission_name_upper = emission_name.upper()
        candidates = []

        # Fill candidates
        for emid, emission in emissions.items():
            candidates.append(str(emid))
            candidates.append(emission.Title.upper())

        # Get close matches
        close_matches = difflib.get_close_matches(emission_name_upper,
                                                  candidates)

        # No match at all
        if not close_matches:
            raise NoMatchException(emission_name)

        # No exact match
        if close_matches[0] != emission_name_upper:
            raise NoMatchException(emission_name, close_matches)

        # Exact match
        for emid, emission in emissions.items():
            if emission_name_upper in [str(emid), emission.Title.upper()]:
                return emission

    def get_episode_by_name(self, emission, episode_name):
        episodes = self.get_emission_episodes(emission)
        episode_name_upper = episode_name.upper()
        candidates = []

        for epid, episode in episodes.items():
            candidates.append(str(epid))
            candidates.append(episode.Title.upper())
            candidates.append(episode.SeasonAndEpisode)

        # Get close matches
        close_matches = difflib.get_close_matches(episode_name_upper,
                                                  candidates)

        # No match at all
        if not close_matches:
            raise NoMatchException(episode_name)

        # No exact match
        if close_matches[0] != episode_name_upper:
            raise NoMatchException(episode_name, close_matches)

        # Got an exact match
        for epid, episode in episodes.items():
            search_items = [
                str(epid),
                episode.Title.upper(),
                episode.SeasonAndEpisode
            ]
            if episode_name_upper in search_items:
                return episode

    def get_emission_episode_from_url(self, url):
        # Try sending the request
        try:
            r = requests.get(url)
        except Exception as e:
            raise ClientError('Cannot open URL "{}"'.format(url))

        if r.status_code != 200:
            msg = 'Opening URL "{}" returned HTTP status {}'.format(url, r.status_code)
            raise ClientError(msg)

        # Extract emission and episode ID from meta tag
        regex = r'<meta\s+content="([^".]+)\.([^"]+)"\s+name="ProfilingEmisodeToken"\s*/>'
        m = re.search(regex, r.text)
        if m is None:
            raise ClientError('Cannot read emission/episode information for URL "{}"'.format(url))

        # Find emission and episode
        emid = m.group(1)
        ep_name = m.group(2)

        try:
            emission = self.get_emission_by_name(emid)
            episode = self.get_episode_by_name(emission, ep_name)
        except NoMatchException as e:
            raise ClientError('Cannot read emission/episode information for URL "{}"'.format(url))

        return emission, episode
