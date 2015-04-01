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

import requests
import toutv.exceptions
import toutv.mapper
import toutv.config
import toutv.bos as bos


class Transport:

    def __init__(self):
        pass

    def set_proxies(self, proxies):
        pass

    def get_emissions(self):
        pass

    def get_emission_episodes(self, emission_id):
        pass

    def get_page_repertoire(self):
        pass

    def search_terms(self, query):
        pass


class JsonTransport(Transport):

    def __init__(self, proxies=None):
        self._mapper = toutv.mapper.JsonMapper()

        self.set_proxies(proxies)

    def set_proxies(self, proxies):
        self._proxies = proxies

    def _do_query(self, endpoint, params={}):
        url = '{}{}'.format(toutv.config.TOUTV_JSON_URL_PREFIX, endpoint)
        timeout = 10

        try:
            r = requests.get(url, params=params, headers=toutv.config.HEADERS,
                             proxies=self._proxies, timeout=timeout)
            if r.status_code != 200:
                code = r.status_code
                raise toutv.exceptions.UnexpectedHttpStatusCodeError(url, code)
        except requests.exceptions.Timeout:
            raise toutv.exceptions.RequestTimeoutError(url, timeout)

        response_obj = r.json()

        return response_obj['d']

    def get_emissions(self):
        emissions = {}

        emissions_dto = self._do_query('GetEmissions')
        for emission_dto in emissions_dto:
            emission = self._mapper.dto_to_bo(emission_dto, bos.Emission)
            emissions[emission.Id] = emission

        return emissions

    def get_emission_episodes(self, emission):
        emid = emission.Id
        episodes = {}
        params = {
            'emissionid': str(emid)
        }

        episodes_dto = self._do_query('GetEpisodesForEmission', params)
        for episode_dto in episodes_dto:
            episode = self._mapper.dto_to_bo(episode_dto, bos.Episode)
            episode.set_emission(emission)
            episodes[episode.Id] = episode

        return episodes

    def get_page_repertoire(self):
        repertoire_dto = self._do_query('GetPageRepertoire')

        repertoire = bos.Repertoire()

        # Emissions
        if 'Emissions' in repertoire_dto:
            repertoire.Emissions = {}
            emissionrepertoires_dto = repertoire_dto['Emissions']
            for emissionrepertoire_dto in emissionrepertoires_dto:
                er = self._mapper.dto_to_bo(emissionrepertoire_dto,
                                            bos.EmissionRepertoire)
                repertoire.Emissions[er.Id] = er

        # Genre
        if 'Genres' in repertoire_dto:
            # TODO: implement
            pass

        # Country
        if 'Pays' in repertoire_dto:
            # TODO: implement
            pass

        return repertoire

    def search(self, query):
        searchresults = None
        searchresultdatas = []
        params = {
            'query': query
        }

        searchresults_dto = self._do_query('SearchTerms', params)

        searchresults = self._mapper.dto_to_bo(searchresults_dto,
                                               bos.SearchResults)
        if searchresults.Results is not None:
            for searchresultdata_dto in searchresults.Results:
                sr_bo = self._mapper.dto_to_bo(searchresultdata_dto,
                                               bos.SearchResultData)
                searchresultdatas.append(sr_bo)
        searchresults.Results = searchresultdatas

        return searchresults
