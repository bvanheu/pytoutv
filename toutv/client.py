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

import os
import json
import platform
import urllib.request
import urllib.parse
import urllib.error
import toutv.cache
import toutv.mapper
import toutv.bos as bos


USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7'
TOUTV_WSDL_URL = 'http://api.tou.tv/v1/TouTVAPIService.svc?wsdl'
TOUTV_PLAYLIST_URL_TMPL = 'http://api.radio-canada.ca/validationMedia/v1/Validation.html?appCode=thePlatform&deviceType=iphone4&connectionType=wifi&idMedia={}&output=json'
TOUTV_JSON_URL = 'https://api.tou.tv/v1/toutvapiservice.svc/json/'


class Transport:
    def __init__(self):
        pass

    def get_emissions(self):
        pass

    def get_emission_episodes(self, emission_id):
        pass

    def get_page_repertoire(self):
        pass

    def search_terms(self, query):
        pass


class TransportJson(Transport):
    def __init__(self):
        self.json_decoder = json.JSONDecoder()
        self.mapper = toutv.mapper.MapperJson()

    def _do_query(self, method, parameters={}):
        parameters_str = urllib.parse.urlencode(parameters)
        url = ''.join([TOUTV_JSON_URL, method, '?', parameters_str])
        headers = {'User-Agent': USER_AGENT}
        request = urllib.request.Request(url, None, headers)
        json_string = urllib.request.urlopen(request).read().decode('utf-8')
        json_decoded = self.json_decoder.decode(json_string)
        return json_decoded['d']

    def get_emissions(self):
        emissions = {}
        emissions_dto = self._do_query('GetEmissions')

        for emission_dto in emissions_dto:
            emission = self.mapper.dto_to_bo(emission_dto, bos.Emission)
            emissions[emission.Id] = emission

        return emissions

    def get_emission_episodes(self, emission_id):
        episodes = {}
        episodes_dto = self._do_query('GetEpisodesForEmission',
                                      {'emissionid': str(emission_id)})

        if episodes_dto:
            for episode_dto in episodes_dto:
                episode = self.mapper.dto_to_bo(episode_dto, bos.Episode)
                episodes[episode.Id] = episode

        return episodes

    def get_page_repertoire(self):
        repertoire = {}
        repertoire_dto = self._do_query('GetPageRepertoire')

        if repertoire_dto:
            # EmissionRepertoire
            if repertoire_dto:
                emissionrepertoires = {}
                for emissionrepertoire_dto in repertoire_dto['Emissions']:
                    er = self.mapper.dto_to_bo(emissionrepertoire_dto,
                                               bos.EmissionRepertoire)
                    emissionrepertoires[er.Id] = er
                repertoire['emissionrepertoire'] = emissionrepertoires
            # Genre
            if repertoire_dto['Genres']:
                pass
            # Country
            if repertoire_dto['Pays']:
                pass

        return repertoire

    def search_terms(self, query):
        searchresults_dto = self._do_query('SearchTerms', {'query': query})
        searchresults = None
        searchresultdatas = []

        if searchresults_dto:
            searchresults = self.mapper.dto_to_bo(searchresults_dto,
                                                  bos.SearchResults)
            if searchresults.Results is not None:
                for searchresultdata_dto in searchresults.Results:
                    sr_bo = self.mapper.dto_to_bo(searchresultdata_dto,
                                                  bos.SearchResultData)
                    searchresultdatas.append(sr_bo)
            searchresults.Results = searchresultdatas

        return searchresults


class Client:
    def __init__(self, transport=TransportJson(),
                 cache=toutv.cache.EmptyCache()):
        self.transport = transport
        self.cache = cache

    def get_emissions(self):
        emissions = self.cache.get('emissions')

        if not emissions:
            emissions = self.transport.get_emissions()
            self.cache.set('emissions', emissions)

        return emissions

    def get_emission_episodes(self, emission_id):
        episodes_per_emission = self.cache.get('episodes')

        if not episodes_per_emission:
            episodes_per_emission = {}
            ep = self.transport.get_emission_episodes(emission_id)
            episodes_per_emission[emission_id] = ep
            self.cache.set('episodes', episodes_per_emission)

        if not (emission_id in episodes_per_emission):
            ep = self.transport.get_emission_episodes(emission_id)
            episodes_per_emission[emission_id] = ep
            self.cache.set('episodes', episodes_per_emission)

        return episodes_per_emission[emission_id]

    def fetch_playlist_url(self, episode_pid):
        url = TOUTV_PLAYLIST_URL_TMPL.format(episode_pid)
        headers = {'User-Agent': USER_AGENT}
        req = urllib.request.Request(url, None, headers)
        json_string = urllib.request.urlopen(req).read().decode('utf-8')
        response = json.loads(json_string)

        if response['errorCode']:
            raise RuntimeError(response['message'])

        return response['url']

    # TODO: implement `use_cache` flag
    def get_page_repertoire(self, use_cache=True):
        repertoire = self.cache.get('repertoire')

        if not repertoire:
            repertoire = self.transport.get_page_repertoire()
            self.cache.set('repertoire', repertoire)

        return repertoire

    def search_terms(self, query):
        return self.transport.search_terms(query)

    def search_terms_max(self, query, max_results):
        pass
