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

import shelve
from datetime import datetime
from datetime import timedelta


class Cache:
    def __init__(self):
        pass

    def get_emissions(self):
        pass

    def get_emission_episodes(self, emission_id):
        pass

    def get_page_repertoire(self):
        pass

    def set_emissions(self, emissions):
        pass

    def set_emission_episodes(self, emission_id, episodes):
        pass

    def set_page_repertoire(self, page_repertoire):
        pass


class EmptyCache(Cache):
    def get_emissions(self):
        return None

    def get_emission_episodes(self, emission_id):
        return None

    def get_page_repertoire(self):
        return None


class CacheShelve(Cache):
    def __init__(self, shelve_filename):
        self.shelve = shelve.open(shelve_filename)

    def __del__(self):
        self.shelve.close()

    def _has_key(self, key):
        if key in self.shelve:
            expire, value = self.shelve[key]
            if datetime.now() < expire:
                return True

        return False

    def _get(self, key):
        if not self._has_key(key):
            return None

        expire, value = self.shelve[key]

        return value

    def _set(self, key, value, expire=timedelta(hours=2)):
        self.shelve[key] = (datetime.now() + expire, value)

    def get_emissions(self):
        return self._get('emissions')

    def get_emission_episodes(self, emission_id):
        emission_episodes = self._get('emission_episodes')
        if emission_episodes is None:
            return None
        if not emission_id in emission_episodes:
            return None

        return emission_episodes[emission_id]

    def get_page_repertoire(self):
        pass

    def set_emissions(self, emissions):
        self._set('emissions', emissions)

    def set_emission_episodes(self, emission_id, episodes):
        emission_episodes = self._get('emission_episodes')
        if emission_episodes is None:
            emission_episodes = {}
        emission_episodes[emission_id] = episodes
        self._set('emission_episodes', emission_episodes)

    def set_page_repertoire(self, page_repertoire):
        pass
