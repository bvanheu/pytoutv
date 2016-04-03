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

from toutv3 import model, model_from_api, cache2
from bs4 import BeautifulSoup
from functools import partial
import requests.cookies
import requests
import logging
import urllib
import json
import sys


_logger = logging.getLogger(__name__)


_HTTP_HEADERS = {
    'User-Agent': 'TouTvApp/2.3.1 (iPhone4.1; iOS/7.1.2; en-ca)'
}
_HTTP_TOUTV_HEADERS = {
    'Accept': 'application/json',
}
_HTTP_TOUTV_GET_PARAMS = {
    'v': '2',
    'd': 'phone-ios',
}
_PRES_SETTINGS_URL = 'http://ici.tou.tv/presentation/settings'
_USER_PROFILE_URL = 'http://ici.tou.tv/profiling/userprofile'


class Agent:
    def __init__(self, user, password, no_cache=False):
        self._user = user
        self._password = password
        self._no_cache = no_cache
        self._toutv_base_params = {}
        self._toutv_base_params.update(_HTTP_TOUTV_GET_PARAMS)
        self._req_session = requests.Session()
        self._model_factory = model_from_api.Factory(self)
        self._load_cache()

    def _load_cache(self):
        if self._no_cache:
            # do not even bother loading a real cache
            _logger.debug("Not loading any cache as per user's request")
            self._cache = cache2.Cache(self._user)
            return

        # load the cache
        self._cache = cache2.load(self._user)

        # update our properties from the cache
        self._req_session.cookies = self._cache.cookies

        if not self._cache.base_headers:
            self._cache.base_headers.update(_HTTP_HEADERS)

        if not self._cache._toutv_base_headers:
            self._cache._toutv_base_headers.update(_HTTP_TOUTV_HEADERS)

    def release_cache(self):
        self._cache.release()

    def _request(self, method, url, data, headers=None, params=None,
                 allow_redirects=True):
        actual_headers = {}
        actual_headers.update(self._cache.base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}

        if params is not None:
            actual_params.update(params)

        fmt = 'HTTP {} request @ "{}" ({} headers, {} params)'
        _logger.debug(fmt.format(method, url, len(actual_headers), len(actual_params)))

        return self._req_session.request(method=method, url=url, data=data,
                                         headers=actual_headers,
                                         params=actual_params,
                                         allow_redirects=allow_redirects)

    def _post(self, url, data, headers=None, params=None, allow_redirects=True):
        return self._request('POST', url, data, headers,
                             params, allow_redirects)

    def _get(self, url, headers=None, params=None, allow_redirects=True):
        return self._request('GET', url, None, headers,
                             params, allow_redirects)

    def _toutv_get(self, url, headers=None, params=None,
                      allow_redirects=True):
        actual_headers = {}
        actual_headers.update(self._cache.toutv_base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}
        actual_params.update(self._toutv_base_params)

        if params is not None:
            actual_params.update(params)

        return self._get(url=url, headers=actual_headers, params=actual_params,
                         allow_redirects=allow_redirects)

    def _register_settings(self):
        if len(self._cache.pres_settings) > 0:
            return

        _logger.debug('Registering settings')
        r = self._toutv_get(_PRES_SETTINGS_URL)
        self._cache.pres_settings = r.json()

    def _get_setting(self, name):
        _logger.debug('Getting setting "{}"'.format(name))
        self._register_settings()

        return self._cache.pres_settings[name]

    def _login(self):
        if self._cache.is_logged_in:
            return

        _logger.debug('Logging in')

        # get a few needed settings
        mobile_scopes = self._get_setting('MobileScopes')
        client_id = self._get_setting('LoginClientIdIos')
        endpoint_auth = self._get_setting('EndpointAuthorizationIos')

        # get login page
        url = '{}?response_type=token&client_id={}&scope={}&state=authCode&redirect_uri=http://ici.tou.tv/profiling/callback'
        url = url.format(endpoint_auth, client_id, mobile_scopes)
        _logger.debug('Getting login page')
        r = self._get(url)
        login_soup = BeautifulSoup(r.text, 'html.parser')

        # fill the form with user creds
        form_login = login_soup.select('#Form-login')[0]
        data = {}

        for input_el in form_login.select('input'):
            if input_el.has_attr('name') and input_el.has_attr('value'):
                data[input_el['name']] = input_el['value']

        data['login-email'] = self._user
        data['login-password'] = self._password
        action = form_login['action']

        # submit the form. this returns a response which includes super
        # secret stuff (auth tokens and shit) in its "Location" header.
        _logger.debug('Submitting login page form')
        r = self._post(action, data, allow_redirects=False)

        # extract said super secret stuff from the fragment
        url_components = urllib.parse.urlparse(r.headers['Location'])
        _logger.debug('Received location: "{}"'.format(r.headers['Location']))
        qs_parts = urllib.parse.parse_qs(url_components.fragment)
        token_type = qs_parts['token_type'][0]
        access_token = qs_parts['access_token'][0]
        _logger.debug('Token type: "{}"'.format(token_type))
        _logger.debug('Access token: "{}"'.format(access_token))

        # update TOU.TV base headers for future requests
        self._cache.toutv_base_headers['Authorization'] = '{} {}'.format(token_type, access_token)
        self._cache.toutv_base_headers['ClientID'] = client_id
        self._cache.toutv_base_headers['RcId'] = ''

        # we're in!
        _logger.debug('Successfully logged in')
        self._cache.is_logged_in = True

    def get_user_infos(self):
        _logger.debug('Getting user infos')
        self._login()

        if self._cache.user_infos is None:
            _logger.debug('Downloading user infos')

            # RC user infos endpoint is a setting
            rc_user_infos_endpoint = self._get_setting('EndpointUserInfoIos')

            # get user infos
            rc_user_infos = self._toutv_get(rc_user_infos_endpoint)
            toutv_user_infos = self._toutv_get(_USER_PROFILE_URL)

            # create user infos object
            self._cache.user_infos = self._model_factory.create_user_infos(rc_user_infos.json(),
                                                                           toutv_user_infos.json())
        else:
            _logger.debug('User infos found in cache')

        return self._cache.user_infos
