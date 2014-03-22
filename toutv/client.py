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

import requests
import json
import toutv.cache
import toutv.mapper
import toutv.transport
import toutv.config
import toutv.bos as bos


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

    def get_emission_episodes(self, emission_id):
        episodes = self.cache.get_emission_episodes(emission_id)
        if episodes is None:
            episodes = self.transport.get_emission_episodes(emission_id)
            self.cache.set_emission_episodes(emission_id, episodes)

        return episodes

    def get_page_repertoire(self):
        page_repertoire = self.cache.get_page_repertoire()
        if page_repertoire is None:
            page_repertoire = self.transport.get_page_repertoire()
            self.cache.set_page_repertoire(page_repertoire)

        return page_repertoire

    def get_episode_playlist_url(self, episode):
        url = toutv.config.TOUTV_PLAYLIST_URL
        headers = {
            'User-Agent': toutv.config.USER_AGENT
        }
        params = dict(toutv.config.TOUTV_PLAYLIST_PARAMS)
        params['idMedia'] = episode.PID

        r = requests.get(url, params=params, headers=headers)
        response_obj = r.json()

        if response_obj['errorCode']:
            raise RuntimeError(response_obj['message'])

        return response_obj['url']

    def search(self, query):
        return self.transport.search(query)
