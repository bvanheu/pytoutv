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

from bs4 import BeautifulSoup
import requests
import logging
import urllib
import json
import sys


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


class Agent:
    def __init__(self, user, password):
        self._user = user
        self._password = password
        self._base_headers = {}
        self._base_headers.update(_HTTP_HEADERS)
        self._toutv_base_headers = {}
        self._toutv_base_headers.update(_HTTP_TOUTV_HEADERS)
        self._toutv_base_params = {}
        self._toutv_base_params.update(_HTTP_TOUTV_GET_PARAMS)
        self._pres_settings = None
        self._logged_in = False
        self._session = requests.Session()

    def _post(url, data, headers=None, params=None, allow_redirects=True):
        actual_headers = {}
        actual_headers.update(self._base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}

        if params is not None:
            actual_params.update(params)

        return self._session.post(url=url, data=data, headers=actual_headers,
                                  params=actual_params,
                                  allow_redirects=allow_redirects)

    def _get(url, headers=None, params=None, allow_redirects=True):
        actual_headers = {}
        actual_headers.update(self._base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}

        if params is not None:
            actual_params.update(params)

        return self._session.get(url=url, headers=actual_headers,
                                 params=actual_params,
                                 allow_redirects=allow_redirects)

    def _toutvapp_get(url, headers=None, params=None, allow_redirects=True):
        actual_headers = {}
        actual_headers.update(self._toutv_base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}
        actual_params.update(self._toutv_base_params)

        if params is not None:
            actual_params.update(params)

        return self._get(url=url, headers=actual_headers, params=params,
                         allow_redirects=allow_redirects)

    def _register_settings(self):
        if self._pres_settings is not None:
            return

        r = self._toutvapp_get(_PRES_SETTINGS_URL)
        self._pres_settings = r.json()

    def _get_setting(self, name):
        self._register_settings()

        return self._pres_settings[name]

    def _login(self):
        if self._logged_in:
            return

        # get a few needed settings
        mobile_scopes = self._get_setting('MobileScopes')
        client_id = self._get_setting('LoginClientIdIos')
        endpoint_auth = self._get_setting('EndpointAuthorizationIos')

        # get login page
        params = {
            'response_type': 'token',
            'client_id': client_id,
            'scope': mobile_scopes,
            'state': 'authCode',
            'redirect_uri': 'http://ici.tou.tv/profiling/callback',
        }
        r = self._get(endpoint_auth, params=params)
        login_soup = BeautifulSoup(r.text, 'html.parser')

        # fill the form with user creds
        form_login = login_soup.soup.select('#Form-login')[0]
        data = {}

        for hidden_field in form_login.select('input[type="hidden"]'):
            data[hidden_field['name']] = hidden_field['value']

        data['login-email'] = self._user
        data['login-password'] = self._password
        action = form_login['action']

        # submit the form. this returns a response which includes super
        # secret stuff (auth tokens and shit) in its "Location" header.
        r = self._post(action, data, allow_redirects=False)

        # extract said super secret stuff from the fragment
        url_components = urllib.parse.urlparse(r.headers['Location'])
        qs_parts = urllib.parse.parse_qs(url_components.fragment)
        token_type = qs_parts['token_type'][0]
        access_token = qs_parts['access_token'][0]

        # update TOU.TV base headers for future requests
        self._toutv_base_headers['Authorization'] = '{} {}'.format(token_type, access_token)
        self._toutv_base_headers['ClientID'] = client_id
        self._toutv_base_headers['RcId'] = ''

        # we're in!
        self._logged_in = True

    def _get_user_infos(self):
        self._login()

        # TODO
        r = _toutvapp_get('http://ici.tou.tv/profiling/userprofile?v=2&d=phone-ios',
                          headers=le_dict)
        r = _toutvapp_get('https://services.radio-canada.ca/openid/connect/v1/userinfo',
                          headers=le_dict)
