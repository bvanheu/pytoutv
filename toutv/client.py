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
import difflib
import toutv.cache
import toutv.mapper
import toutv.transport
import toutv.config
import toutv.dl


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
                 cache=toutv.cache.EmptyCache(), proxies=None, auth=None):
        self._transport = transport
        self._cache = cache

        self.set_proxies(proxies)
        self.set_auth(auth)

    def set_proxies(self, proxies):
        self._proxies = proxies
        self._transport.set_proxies(proxies)

    def set_auth(self, auth):
        self._auth = auth
        self._transport.set_auth(auth)

    def _set_bo_proxies(self, bo):
        bo.set_proxies(self._proxies)

    def _set_bos_proxies(self, bos):
        for bo in bos:
            self._set_bo_proxies(bo)

    def _set_bo_auth(self, bo):
        bo.set_auth(self._auth)

    def _set_bos_auth(self, bos):
        for bo in bos:
            self._set_bo_auth(bo)

    def get_emissions(self):
        emissions = self._cache.get_emissions()
        if emissions is None:
            emissions = self._transport.get_emissions()
            self._cache.set_emissions(emissions)

        self._set_bos_proxies(emissions)
        self._set_bos_auth(emissions)

        return emissions

    def get_emission_episodes(self, emission, short_version=False):
        episodes = None
        if short_version:
            episodes = self._cache.get_emission_episodes(emission)
        if episodes is None:
            episodes = self._transport.get_emission_episodes(emission, short_version)
            if short_version:
                self._cache.set_emission_episodes(emission, episodes)

        self._set_bos_proxies(episodes)
        self._set_bos_auth(episodes)

        return episodes

    def search(self, query):
        search = self._transport.search(query)
        self._set_bo_proxies(search)

        # Add local emissions (to find Extra emissions & episodes)
        emissions = self.get_emissions()
        query_upper = query.upper()
        for emission in emissions:
            if query_upper in emission.get_title().upper():
                try:
                    # Load this emission' episodes, and add those to the search results too
                    episodes = self._transport.get_emission_episodes(emission, True)

                    sr = toutv.bos.SearchResultData()
                    sr.Emission = emission
                    search.Results.append(sr)

                    for episode in episodes:
                        sr = toutv.bos.SearchResultData()
                        sr.Episode = episode
                        search.Results.append(sr)
                except toutv.exceptions.UnexpectedHttpStatusCodeError as e:
                    if e.status_code == 404:
                        # Show returned by search was not found on new API; just skip this result
                        pass
                    else:
                        raise e

        return search

    def get_emission_by_whatever(self, query):
        shows = self.get_emissions()
        query_upper = query.upper()
        # Map candidates to shows, so that when we get a match between the
        # query string and a candidate string, it's easy to go back to the<
        # corresponding show.
        candidates_to_shows = {}

        # Fill candidates
        for show in shows:
            candidates_to_shows[str(show.get_id())] = show
            candidates_to_shows[show.get_title().upper()] = show
            # The Url property looks like '/infoman', so we strip the leading /.
            candidates_to_shows[show.Url.upper()[1:]] = show

        # Get close matches
        close_matches = difflib.get_close_matches(
            query_upper, candidates_to_shows.keys())

        if not close_matches:
            # No match at all
            raise NoMatchException(query)

        # Matches are sorted by how close they look like the query, so if we
        # have an exact match, it should be first in the list.
        first_match = close_matches[0]
        if first_match != query_upper:
            # No exact match
            raise NoMatchException(query, close_matches)

        # There is an exact match! Return the corresponding show.
        return candidates_to_shows[first_match]

    def get_episode_by_name(self, emission, episode_name, short_version=False):
        episodes = self.get_emission_episodes(emission, short_version)
        episode_name_upper = episode_name.upper()
        candidates = []

        for episode in episodes:
            candidates.append(str(episode.get_id()))
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
        for episode in episodes:
            search_items = [
                str(episode.get_id()),
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
