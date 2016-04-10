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

from toutv3 import model, model_from_api, cache, playlist, download
from bs4 import BeautifulSoup
from functools import partial
import requests.cookies
import requests
import logging
import toutv3
import urllib
import json
import sys


_logger = logging.getLogger(__name__)


_VALID_HTTP_STATUS_CODES = (200, 301, 302)
_HTTP_HEADERS = {
    'User-Agent': 'TouTvApp/2.3.1 (iPhone4.1; iOS/7.1.2; en-ca)',
}
_HTTP_TOUTV_HEADERS = {
    'Accept': 'application/json',
}
_HTTP_AKAMAIHD_HEADERS = {
    'User-Agent': 'AppleCoreMedia/1.0.0.11D257 (iPhone; U; CPU OS 7_1_2 like Mac OS X; en_us)',
}
_HTTP_TOUTV_GET_PARAMS = {
    'v': '2',
    'd': 'phone-ios',
}
_TOUTV_URL = 'http://ici.tou.tv'
_PRES_BASE_URL = '{}/presentation'.format(_TOUTV_URL)
_PRES_SETTINGS_URL = '{}/settings'.format(_PRES_BASE_URL)
_USER_PROFILE_URL = '{}/profiling/userprofile'.format(_TOUTV_URL)
_SEARCH_URL = '{}/search'.format(_PRES_BASE_URL)
_SECTION_URL = '{}/section'.format(_PRES_BASE_URL)


class _Agent:
    def __init__(self, user, password, no_cache=False):
        self._user = user
        self._password = password
        self._no_cache = no_cache
        self._toutv_base_params = {}
        self._toutv_base_params.update(_HTTP_TOUTV_GET_PARAMS)
        self._req_session = requests.Session()
        self._model_factory = model_from_api._Factory(self)
        self._logging_in = False
        self._load_cache()

    def _set_cache_objects_agent(self):
        # the loaded cache objects have no registered agent (the agent
        # is not serialized), thus we need to set their agent as the
        # current agent, otherwise they are not complete.
        if self._cache.user_infos:
            self._cache.user_infos._set_agent(self)

        for section_summary in self._cache.section_summaries.values():
            section_summary._set_agent(self)

        for search_show_summary in self._cache.search_show_summaries:
            search_show_summary._set_agent(self)

        for section in self._cache.sections.values():
            section._set_agent(self)

        for show in self._cache.shows.values():
            show._set_agent(self)

    def _load_cache(self):
        if self._no_cache:
            # do not even bother loading a real cache
            _logger.debug("Not loading any cache as per user's request")
            self._cache = cache._Cache(self._user)
            return

        # load the cache
        self._cache = cache._load(self._user)

        # set the current agent as the cache objects's agent
        self._set_cache_objects_agent()

        # update our properties from the cache
        self._req_session.cookies = self._cache.cookies

        if not self._cache.base_headers:
            self._cache.base_headers.update(_HTTP_HEADERS)

        if not self._cache._toutv_base_headers:
            self._cache._toutv_base_headers.update(_HTTP_TOUTV_HEADERS)

    def release_cache(self):
        self._cache.release()

    def _request(self, method, url, data, headers=None, params=None,
                 allow_redirects=True, stream=False):
        actual_headers = {}
        actual_headers.update(self._cache.base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}

        if params is not None:
            actual_params.update(params)

        fmt = 'HTTP {} request @ "{}" ({} headers, {} params)'
        _logger.debug(fmt.format(method, url, len(actual_headers), len(actual_params)))

        try:
            response = self._req_session.request(method=method, url=url, data=data,
                                                 headers=actual_headers,
                                                 params=actual_params,
                                                 allow_redirects=allow_redirects,
                                                 stream=stream)

            if stream:
                fmt = 'HTTP response, streaming mode (status code: {})'
                _logger.debug(fmt.format(response.status_code))
            else:
                fmt = 'HTTP response (status code: {}, content length: {} bytes)'
                _logger.debug(fmt.format(response.status_code, len(response.content)))

            return response
        except Exception as e:
            # wrap requests exception
            if isinstance(e, requests.Timeout):
                exc_cls = toutv3.NetworkTimeout
            elif isinstance(e, requests.ConnectionError):
                exc_cls = toutv3.ConnectionError
            else:
                exc_cls = toutv3.HttpError

            exc = exc_cls(method, url, data, headers, params, allow_redirects)
            raise exc from e

    def _post(self, url, data, headers=None, params=None, allow_redirects=True):
        return self._request('POST', url, data, headers,
                             params, allow_redirects)

    def _get(self, url, headers=None, params=None, allow_redirects=True,
             stream=False):
        return self._request('GET', url, None, headers,
                             params, allow_redirects, stream)

    def _toutv_get(self, url, headers=None, params=None,
                   allow_redirects=True, stream=False):
        actual_headers = {}
        actual_headers.update(self._cache.toutv_base_headers)

        if headers is not None:
            actual_headers.update(headers)

        actual_params = {}
        actual_params.update(self._toutv_base_params)

        if params is not None:
            actual_params.update(params)

        r = self._get(url=url, headers=actual_headers, params=actual_params,
                      allow_redirects=allow_redirects)

        if self._logging_in:
            # we're in the process of logging in, so do not care about
            # trying to login again
            return r

        if r.status_code not in _VALID_HTTP_STATUS_CODES:
            # no need to login again with 404: the resource is not found
            if r.status_code == 404:
                exc_cls = toutv3.UnexpectedHttpStatusCode
                raise exc_cls(r.status_code, 'GET', url, None, headers,
                              params, allow_redirects)

            # bad request/unauthorized: try logging in and retry the
            # GET request
            _logger.debug('Trying to login again')
            self._cache.is_logged_in = False
            self._login()

            # logged in now: self._login() either succeeds, or raises
            # an exception
            r = self._get(url=url, headers=actual_headers,
                          params=actual_params,
                          allow_redirects=allow_redirects, stream=stream)

            if r.status_code not in _VALID_HTTP_STATUS_CODES:
                # still not working: we have a serious problem
                exc_cls = toutv3.UnexpectedHttpStatusCode
                raise exc_cls(r.status_code, 'GET', url, None, headers,
                              params, allow_redirects)

        return r

    def _akamaihd_get(self, url, stream=False):
        r = self._get(url=url, headers=_HTTP_AKAMAIHD_HEADERS,
                      stream=stream)

        if r.status_code != 200:
            raise UnexpectedHttpStatusCode(r.status_code, 'GET', url,
                                           None, headers, None, False)

        return r

    def akamaihd_stream_get(self, url, chunk_size):
        r = self._akamaihd_get(url, True)

        for chunk in r.iter_content(chunk_size):
            yield chunk

    def _register_settings(self):
        _logger.debug('Registering settings')

        if len(self._cache.pres_settings) > 0:
            _logger.debug('Settings found in cache')
            return

        _logger.debug('Requesting settings')
        r = self._toutv_get(_PRES_SETTINGS_URL)

        if r.status_code != 200:
            _logger.error('Cannot register settings')
            raise toutv3.ApiChanged()

        try:
            self._cache.pres_settings = r.json()
        except:
            _logger.error('Cannot decode settings')
            raise toutv3.ApiChanged()

        _logger.debug('Registered settings')

    def _get_setting(self, name):
        _logger.debug('Getting setting "{}"'.format(name))
        self._register_settings()

        try:
            setting = self._cache.pres_settings[name]
        except:
            _logger.error('Cannot find setting "{}"'.format(name))
            raise toutv3.ApiChanged()

        _logger.debug('Found "{}" setting value: "{}"'.format(name, setting))

        return setting

    def _do_login(self):
        _logger.debug('Trying to log in')

        if self._cache.is_logged_in:
            _logger.debug('Already logged in')
            return

        # get a few needed settings
        mobile_scopes = self._get_setting('MobileScopes')
        client_id = self._get_setting('LoginClientIdIos')
        endpoint_auth = self._get_setting('EndpointAuthorizationIos')

        # get login page
        url = '{}?response_type=token&client_id={}&scope={}&state=authCode&redirect_uri=http://ici.tou.tv/profiling/callback'
        url = url.format(endpoint_auth, client_id, mobile_scopes)
        _logger.debug('Requesting login page')
        r = self._get(url)

        if r.status_code != 200:
            _logger.error('Failed to request login page')
            raise toutv3.ApiChanged()

        try:
            login_soup = BeautifulSoup(r.text, 'html.parser')
        except:
            _logger.error('Cannot parse login page')
            raise toutv3.ApiChanged()

        # fill the form with user creds
        try:
            form_login = login_soup.select('#Form-login')[0]
        except:
            _logger.error('Login page: cannot select login form')
            raise toutv3.ApiChanged()

        data = {}

        for input_el in form_login.select('input'):
            if input_el.has_attr('name') and input_el.has_attr('value'):
                data[input_el['name']] = input_el['value']

        data['login-email'] = self._user
        data['login-password'] = self._password

        try:
            action = form_login['action']
        except:
            _logger.error("Login page: cannot get login form's action")
            raise toutv3.ApiChanged()

        # submit the form. this returns a response which includes super
        # secret stuff (auth tokens and shit) in its "Location" header.
        _logger.debug('Submitting login page form')
        r = self._post(action, data, allow_redirects=False)

        # success?
        if r.status_code not in (301, 302):
            _logger.error('Got HTTP status {}: invalid credentials'.format(r.status_code))
            raise toutv3.InvalidCredentials(self._user, self._password)

        # extract said super secret stuff from the fragment
        try:
            url_components = urllib.parse.urlparse(r.headers['Location'])
        except:
            _logger.error('Cannot parse URL in "Location" header')
            raise toutv3.ApiChanged()

        _logger.debug('Received location: "{}"'.format(r.headers['Location']))
        qs_parts = urllib.parse.parse_qs(url_components.fragment)

        try:
            token_type = qs_parts['token_type'][0]
        except:
            _logger.error('Cannot get "token_type" part of query string')
            raise toutv3.ApiChanged()

        try:
            self._cache._access_token = qs_parts['access_token'][0]
        except:
            _logger.error('Cannot get "access_token" part of query string')
            raise toutv3.ApiChanged()

        _logger.debug('Token type: "{}"'.format(token_type))
        _logger.debug('Access token: "{}"'.format(self._cache._access_token))

        # update TOU.TV base headers for future requests
        authorization = '{} {}'.format(token_type, self._cache._access_token)
        self._cache.toutv_base_headers['Authorization'] = authorization
        self._cache.toutv_base_headers['ClientID'] = client_id
        self._cache.toutv_base_headers['RcId'] = ''

        # we're in!
        self._cache.is_logged_in = True
        _logger.debug('Successfully logged in')

    def _login(self):
        self._logging_in = True

        try:
            self._do_login()
        finally:
            self._logging_in = False

    def get_user_infos(self):
        _logger.debug('Getting user infos')

        if self._cache.user_infos:
            _logger.debug('User infos found in cache')
            return self._cache.user_infos

        self._login()

        # RC user infos endpoint is a setting
        rc_user_infos_endpoint = self._get_setting('EndpointUserInfoIos')

        # get user infos
        _logger.debug('Requesting RC user infos')
        r_rc_user_infos = self._toutv_get(rc_user_infos_endpoint)

        if r_rc_user_infos.status_code != 200:
            _logger.error('Failed to request RC user infos')
            raise toutv3.ApiChanged()

        _logger.debug('Requesting TOU.TV user profile')
        r_toutv_user_infos = self._toutv_get(_USER_PROFILE_URL)

        if r_toutv_user_infos.status_code != 200:
            _logger.error('Failed to request TOU.TV user profile')
            raise toutv3.ApiChanged()

        # decode user infos
        try:
            rc_user_infos = r_rc_user_infos.json()
        except:
            _logger.error('Cannot decode RC user infos (JSON)')
            raise toutv3.ApiChanged()

        try:
            toutv_user_infos = r_toutv_user_infos.json()
        except:
            _logger.error('Cannot decode TOU.TV user profile (JSON)')
            raise toutv3.ApiChanged()

        # create user infos object
        try:
            func = self._model_factory.create_user_infos
            self._cache.user_infos = func(rc_user_infos, toutv_user_infos)
        except:
            _logger.error('Cannot create user infos object')
            raise toutv3.ApiChanged()

        _logger.debug('Created user infos object')

        return self._cache.user_infos

    def get_search_show_summaries(self):
        _logger.debug('Getting search show summaries')

        if self._cache.search_show_summaries:
            _logger.debug('Search show summaries found in cache')
            return self._cache.search_show_summaries

        self._login()
        _logger.debug('Requesting search show summaries')

        # get search show summaries
        r_sss = self._toutv_get(_SEARCH_URL)

        if r_sss.status_code != 200:
            _logger.error('Failed to request search show summaries')
            raise toutv3.ApiChanged()

        # decode search show summaries
        try:
            sss = r_sss.json()
        except:
            _logger.error('Cannot decode search show summaries (JSON)')
            raise toutv3.ApiChanged()

        if type(sss) is not list:
            _logger.error('Cannot decode search show summaries: expecting an array')
            raise toutv3.ApiChanged()

        # create search show summaries objects
        search_show_summaries = []

        for index, sss_item in enumerate(sss):
            try:
                func = self._model_factory.create_search_show_summary
                search_show_summary = func(sss_item)
            except:
                _logger.error('Cannot create search show summary object #{}'.format(index))
                raise toutv3.ApiChanged()

            search_show_summaries.append(search_show_summary)

        self._cache.search_show_summaries = search_show_summaries
        _logger.debug('Created all search show summary objects')

        return self._cache.search_show_summaries

    def get_section_summaries(self):
        _logger.debug('Getting section summaries')

        if self._cache.section_summaries:
            _logger.debug('Section summaries found in cache')
            return self._cache.section_summaries

        self._login()
        _logger.debug('Requesting section summaries')

        # get section summaries
        r_ss = self._toutv_get(_SECTION_URL)

        if r_ss.status_code != 200:
            _logger.error('Failed to request section summaries')
            raise toutv3.ApiChanged()

        # decode section summaries
        try:
            ss = r_ss.json()
        except:
            _logger.error('Cannot decode section summaries (JSON)')
            raise toutv3.ApiChanged()

        if type(ss) is not list:
            _logger.error('Cannot decode section summaries: expecting an array')
            raise toutv3.ApiChanged()

        # create section summaries objects
        for index, ss_item in enumerate(ss):
            try:
                func = self._model_factory.create_section_summary
                section_summary = func(ss_item)
            except:
                _logger.error('Cannot create section summary object #{}'.format(index))
                raise toutv3.ApiChanged()

            self._cache.section_summaries[section_summary.name] = section_summary

        _logger.debug('Created all section summary objects')

        return self._cache.section_summaries

    def get_section(self, name):
        _logger.debug('Getting section "{}"'.format(name))

        if self._cache.get_section(name):
            _logger.debug('Section "{}" found in cache'.format(name))
            return self._cache.get_section(name)

        self._login()
        _logger.debug('Requesting section "{}"'.format(name))

        # get section
        fmt = '{}/{}?smallWidth=220&mediumWidth=600&largeWidth=800&includePartnerTeaser=true'
        url = fmt.format(_SECTION_URL, name)
        r_section = self._toutv_get(url)

        if r_section.status_code != 200:
            _logger.error('Failed to request section')
            raise toutv3.ApiChanged()

        # decode section
        try:
            section = r_section.json()
        except:
            _logger.error('Cannot decode section (JSON)')
            raise toutv3.ApiChanged()

        # create section object
        try:
            section_obj = self._model_factory.create_section(section)
        except:
            _logger.error('Cannot create section object')
            raise toutv3.ApiChanged()

        self._cache.set_section(section_obj)
        _logger.debug('Created section object')

        return self._cache.get_section(name)

    def get_show(self, url_name):
        if not url_name.startswith('/'):
            url_name = '/{}'.format(url_name)

        _logger.debug('Getting show "{}"'.format(url_name))

        if self._cache.get_show(url_name):
            _logger.debug('Show "{}" found in cache'.format(url_name))
            return self._cache.get_show(url_name)

        self._login()
        _logger.debug('Requesting show "{}"'.format(url_name))

        # get show
        fmt = '{}/{}?excludeLineups=False&smallWidth=220&mediumWidth=600&largeWidth=800'
        url = fmt.format(_PRES_BASE_URL, url_name)
        r_show = self._toutv_get(url)

        if r_show.status_code != 200:
            _logger.error('Failed to request show')
            raise toutv3.ApiChanged()

        # decode show
        try:
            show = r_show.json()
        except:
            _logger.error('Cannot decode show (JSON)')
            raise toutv3.ApiChanged()

        # create show object
        try:
            show_obj = self._model_factory.create_show(show)
        except:
            _logger.error('Cannot create show object')
            raise toutv3.ApiChanged()

        self._cache.set_show(url_name, show_obj)
        _logger.debug('Created show object')

        return self._cache.get_show(url_name)

    def _register_claims(self):
        _logger.debug('Registering claims')

        if self._cache.claims:
            _logger.debug('Claims found in cache')
            return

        self._login()
        _logger.debug('Requesting claims')

        # validation endpoint is a setting
        validation_endpoint = self._get_setting('EndpointValidationMediaIos')

        # get claims
        url = '{}/GetClaims'.format(validation_endpoint)
        params = {
            'token': self._cache.access_token,
        }
        r_claims = self._toutv_get(url, params=params)

        if r_claims.status_code != 200:
            _logger.error('Failed to request claims')
            raise toutv3.ApiChanged()

        # decode claims
        try:
            self._cache.claims = r_claims.json()
        except:
            _logger.error('Cannot decode claims (JSON)')
            raise toutv3.ApiChanged()

        _logger.debug('Registered claims')

    def _get_master_playlist(self, id_media):
        _logger.debug('Getting master playlist for media ID "{}"'.format(id_media))
        unsupported_msg = 'Downloading DRM-protected content is unsupported (media ID "{}")'.format(id_media)

        if self._cache.get_master_playlist(id_media):
            _logger.debug('Master playlist for media ID "{}" found in cache'.format(id_media))
            return self._cache.get_master_playlist(id_media)

        if self._cache.get_master_playlist(id_media) is False:
            _logger.error(unsupported_msg)
            raise toutv3.UnsupportedMedia(unsupported_msg)

        self._register_claims()

        if 'claims' not in self._cache.claims:
            _logger.error('Cannot find claims key in claims object')
            raise touv3.ApiChanged()

        params = {
            'appCode': 'toutv',
            'deviceType': 'ioscenc',
            'connectionType': 'wifi',
            'idMedia': id_media,
            'claims': self._cache.claims['claims'],
            'output': 'json',
            'deviceId': str(self._cache.device_id).upper(),
        }

        # validation endpoint is a setting
        validation_endpoint = self._get_setting('EndpointValidationMediaIos')

        # get master playlist info
        _logger.debug('Requesting master playlist info')
        r_playlist_info = self._toutv_get(validation_endpoint, params=params)

        if r_playlist_info.status_code != 200:
            _logger.error('Failed to request master playlist info')
            raise toutv3.ApiChanged()

        # decode playlist info
        try:
            playlist_info = r_playlist_info.json()
        except:
            _logger.error('Cannot decode master playlist info (JSON)')
            raise toutv3.ApiChanged()

        # check for DRM-protected content
        if 'params' in playlist_info:
            try:
                terms = ('drm', 'playready', 'fairplay', 'protection')

                for param in playlist_info['params']:
                    name = param['name']
                    value = param['value']

                    for term in terms:
                        if term in name or term in value:
                            self._cache.set_master_playlist(id_media, False)
                            _logger.error(unsupported_msg)
                            raise toutv3.UnsupportedMedia(unsupported_msg)
            except:
                _logger.error('Cannot decode master playlist parameters')
                raise toutv3.ApiChanged()

        if 'url' not in playlist_info:
            _logger.error('Cannot find URL in master playlist')
            raise toutv3.ApiChanged()

        playlist_url = playlist_info['url']

        if type(playlist_url) is not str:
            _logger.error('Invalid master playlist URL: {}'.format(playlist_url))
            raise toutv3.ApiChanged()

        _logger.debug('Found master playlist URL: "{}"'.format(playlist_url))
        _logger.debug('Requesting master playlist')
        r_playlist = self._akamaihd_get(playlist_url)

        if r_playlist.status_code != 200:
            _logger.error('Failed to request master playlist')
            raise toutv3.ApiChanged()

        try:
            master_playlist = playlist.from_m3u8(r_playlist.text)
        except Exception as e:
            _logger.error('Failed to parse master playlist M3U8')
            raise toutv3.ApiChanged() from e

        if type(master_playlist) is not playlist.MasterPlaylist:
            _logger.error('Expecting a master playlist, got something else')
            raise toutv3.ApiChanged()

        _logger.debug('Created master playlist for media ID "{}"'.format(id_media))
        self._cache.set_master_playlist(id_media, master_playlist)

        return master_playlist

    def get_media_versions(self, id_media):
        _logger.debug('Getting media versions for media ID "{}"'.format(id_media))
        master_playlist = self._get_master_playlist(id_media)
        media_versions = []

        for vs in master_playlist.variant_streams:
            media_versions.append(model.MediaVersion(self, id_media, vs))

        _logger.debug('Created media versions for media ID "{}"'.format(id_media))

        return media_versions

    def _get_playlist(self, uri):
        _logger.debug('Requesting playlist "{}"'.format(uri))
        r_playlist = self._akamaihd_get(uri)

        if r_playlist.status_code != 200:
            _logger.error('Failed to request playlist')
            raise toutv3.ApiChanged()

        try:
            pl = playlist.from_m3u8(r_playlist.text)
        except Exception as e:
            _logger.error('Failed to parse playlist M3U8')
            raise toutv3.ApiChanged() from e

        if type(pl) is not playlist.Playlist:
            _logger.error('Expecting a playlist, got something else')
            raise toutv3.ApiChanged()

        _logger.debug('Created playlist from URL "{}"'.format(uri))

        return pl

    def get_media_segment_key(self, uri):
        _logger.debug('Getting media segment key "{}"'.format(uri))

        if self._cache.get_media_segment_key(uri):
            _logger.debug('Media segment key "{}" found in cache'.format(uri))
            return self._cache.get_media_segment_key(uri)

        _logger.debug('Requesting media segment key "{}"'.format(uri))
        r_key = self._akamaihd_get(uri)

        if r_key.status_code != 200:
            _logger.error('Failed to request media segment key')
            raise toutv3.ApiChanged()

        key = r_key.content

        if len(key) != 16:
            _logger.error('Unexpected media segment key response size: {}'.format(len(key)))
            raise toutv3.ApiChanged()

        self._cache.set_media_segment_key(uri, key)
        _logger.debug('Received media segment key from URL "{}"'.format(uri))

        return key

    def get_download(self, variant_stream):
        _logger.debug('Creating download for variant stream "{}"'.format(variant_stream.uri))

        return download.Download(self, self._get_playlist(variant_stream.uri))
