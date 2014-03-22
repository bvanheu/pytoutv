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

import urllib.request
import json
import toutv.cache
import toutv.mapper
import toutv.transport
import toutv.config
import toutv.bos as bos


class Client:
    def __init__(self, transport=toutv.transport.TransportJson(),
                 cache=toutv.cache.EmptyCache()):
        self.transport = transport
        self.cache = cache

    def get_emissions(self):
        emissions = self.cache.get('emissions')

        if emissions is None:
            emissions = self.transport.get_emissions()
            self.cache.set('emissions', emissions)

        return emissions

    def get_emission_episodes(self, emission_id):
        episodes_per_emission = self.cache.get('episodes')

        if episodes_per_emission is None:
            episodes_per_emission = {}
            ep = self.transport.get_emission_episodes(emission_id)
            episodes_per_emission[emission_id] = ep
            self.cache.set('episodes', episodes_per_emission)

        if not emission_id in episodes_per_emission:
            ep = self.transport.get_emission_episodes(emission_id)
            episodes_per_emission[emission_id] = ep
            self.cache.set('episodes', episodes_per_emission)

        return episodes_per_emission[emission_id]

    def fetch_playlist_url(self, episode_pid):
        url = toutv.config.TOUTV_PLAYLIST_URL_TMPL.format(episode_pid)
        headers = {'User-Agent': toutv.config.USER_AGENT}
        req = urllib.request.Request(url, None, headers)
        json_string = urllib.request.urlopen(req).read().decode('utf-8')
        response = json.loads(json_string)

        if response['errorCode']:
            raise RuntimeError(response['message'])

        return response['url']

    # TODO: implement `use_cache` flag
    def get_page_repertoire(self, use_cache=True):
        repertoire = self.cache.get('repertoire')

        if repertoire is None:
            repertoire = self.transport.get_page_repertoire()
            self.cache.set('repertoire', repertoire)

        return repertoire

    def search_terms(self, query):
        return self.transport.search_terms(query)

    def search_terms_max(self, query, max_results):
        pass
