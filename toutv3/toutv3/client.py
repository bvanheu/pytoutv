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

import os
import re
import difflib
import requests
import toutv.cache
import toutv.mapper
import toutv.transport
import toutv.config
import toutv.dl
from toutv import m3u8


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
                 cache=toutv.cache.EmptyCache(), proxies=None):
        self._transport = transport
        self._cache = cache

        self.set_proxies(proxies)

    def set_proxies(self, proxies):
        self._proxies = proxies
        self._transport.set_proxies(proxies)

    def _set_bo_proxies(self, bo):
        bo.set_proxies(self._proxies)

    def _set_bos_proxies(self, bos):
        for bo in bos:
            self._set_bo_proxies(bo)

    def get_emissions(self):
        emissions = self._cache.get_emissions()
        if emissions is None:
            emissions = self._transport.get_emissions()
            self._cache.set_emissions(emissions)

        self._set_bos_proxies(emissions.values())

        return emissions

    def get_emission_episodes(self, emission):
        episodes = self._cache.get_emission_episodes(emission)
        if episodes is None:
            episodes = self._transport.get_emission_episodes(emission)
            self._cache.set_emission_episodes(emission, episodes)

        self._set_bos_proxies(episodes.values())

        return episodes

    def get_page_repertoire(self):
        # Get repertoire emissions
        page_repertoire = self._cache.get_page_repertoire()
        if page_repertoire is None:
            page_repertoire = self._transport.get_page_repertoire()
            self._cache.set_page_repertoire(page_repertoire)
        rep_em = page_repertoire.get_emissions()

        # Get all emissions (contain more infos) to match them
        all_em = self.get_emissions()

        # Get more infos for repertoire emissions
        emissions = {k: all_em[k] for k in all_em if k in rep_em}
        page_repertoire.set_emissions(emissions)

        # Set proxies
        self._set_bos_proxies(emissions.values())

        return page_repertoire

    def search(self, query):
        search = self._transport.search(query)
        self._set_bo_proxies(search)

        return search

    def get_emission_by_name(self, emission_name):
        emissions = self.get_emissions()
        emission_name_upper = emission_name.upper()
        candidates = []

        # Fill candidates
        for emid, emission in emissions.items():
            candidates.append(str(emid))
            candidates.append(emission.get_title().upper())

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
            exact_matches = [str(emid), emission.get_title().upper()]
            if emission_name_upper in exact_matches:
                return emission

    def get_episode_by_name(self, emission, episode_name):
        episodes = self.get_emission_episodes(emission)
        episode_name_upper = episode_name.upper()
        candidates = []

        for epid, episode in episodes.items():
            candidates.append(str(epid))
            candidates.append(episode.get_title().upper())
            candidates.append(episode.get_sae())

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
                episode.get_title().upper(),
                episode.get_sae()
            ]
            if episode_name_upper in search_items:
                return episode

    @staticmethod
    def _find_last(regex, text):
        results = re.findall(regex, text)
        if not results:
            return None

        return results[-1]

    def get_episode_from_url(self, url):
        # Try sending the request
        timeout = 10

        try:
            r = requests.get(url, proxies=self._proxies, timeout=timeout)
            if r.status_code != 200:
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url,
                                                                     r.status_code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, timeout)

        # Extract emission ID
        regex = r'program-(\d+)'
        emission_m = Client._find_last(regex, r.text)
        if emission_m is None:
            raise ClientError('Cannot read emission information for URL "{}"'.format(url))

        # Extract episode ID
        regex = r'media-(\d+)'
        episode_m = Client._find_last(regex, r.text)
        if episode_m is None:
            raise ClientError('Cannot read episode information for URL "{}"'.format(url))

        # Find emission and episode
        emid = emission_m
        ep_name = episode_m

        try:
            emission = self.get_emission_by_name(emid)
            episode = self.get_episode_by_name(emission, ep_name)
        except NoMatchException as e:
            raise ClientError('Cannot read emission/episode information for URL "{}"'.format(url))

        return episode
