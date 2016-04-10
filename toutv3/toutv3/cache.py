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

from collections import OrderedDict
import requests.cookies
import datetime as DT
import platform
import filelock
import hashlib
import logging
import os.path
import pickle
import uuid
import re


_logger = logging.getLogger(__name__)


class _Cache:
    def __init__(self, user, lock=None):
        if lock is None:
            lock_info = 'without lock'
        else:
            lock_info = 'with lock file "{}"'.format(lock.lock_file)

        _logger.debug('Creating empty cache for user "{}" {}'.format(user, lock_info))
        self._user = user
        self._lock = lock
        self._expire_dt = None
        self._base_headers = {}
        self._toutv_base_headers = {}
        self._cookies = requests.cookies.RequestsCookieJar()
        self._pres_settings = {}
        self._access_token = None
        self._claims = None
        self._is_logged_in = False
        self._shows = {}
        self._sections = {}
        self._master_playlists = {}
        self._media_segment_keys = {}
        self._search_show_summaries = []
        self._section_summaries = OrderedDict()
        self._user_infos = None
        self._device_id = uuid.uuid4()

    @property
    def is_expired(self):
        if self._expire_dt is None:
            return False

        return DT.datetime.now() >= self._expire_dt

    @property
    def expire_dt(self):
        return self._expire_dt

    @property
    def lock(self):
        return self._lock

    @lock.setter
    def lock(self, lock):
        self._lock = lock

    @property
    def device_id(self):
        return self._device_id

    @property
    def pres_settings(self):
        return self._pres_settings

    @pres_settings.setter
    def pres_settings(self, pres_settings):
        self._pres_settings = pres_settings

    @property
    def is_logged_in(self):
        return self._is_logged_in

    @is_logged_in.setter
    def is_logged_in(self, is_logged_in):
        self._is_logged_in = is_logged_in

    @property
    def user_infos(self):
        return self._user_infos

    @user_infos.setter
    def user_infos(self, user_infos):
        self._user_infos = user_infos

    @property
    def base_headers(self):
        return self._base_headers

    @base_headers.setter
    def base_headers(self, headers):
        self._base_headers = headers

    @property
    def toutv_base_headers(self):
        return self._toutv_base_headers

    @toutv_base_headers.setter
    def toutv_base_headers(self, headers):
        self._toutv_base_headers = headers

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    def cookies(self, cookies):
        self._cookies = cookies

    @property
    def claims(self):
        return self._claims

    @claims.setter
    def claims(self, claims):
        self._claims = claims

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, access_token):
        self._access_token = access_token

    @property
    def section_summaries(self):
        return self._section_summaries

    @section_summaries.setter
    def section_summaries(self, section_summaries):
        self._section_summaries = section_summaries

    @property
    def search_show_summaries(self):
        return self._search_show_summaries

    @search_show_summaries.setter
    def search_show_summaries(self, search_show_summaries):
        self._search_show_summaries = search_show_summaries

    @property
    def shows(self):
        return self._shows

    def get_show(self, url_name):
        if url_name in self._shows:
            return self._shows[url_name]

    def set_show(self, url_name, show):
        self._shows[url_name] = show

    @property
    def sections(self):
        return self._sections

    def get_section(self, name):
        if name in self._sections:
            return self._sections[name]

    def set_section(self, section):
        self._sections[section.name] = section

    @property
    def master_playlists(self):
        return self._master_playlists

    def get_master_playlist(self, id_media):
        if id_media in self._master_playlists:
            return self._master_playlists[id_media]

    def set_master_playlist(self, id_media, master_playlist):
        self._master_playlists[id_media] = master_playlist

    @property
    def media_segment_keys(self):
        return self._media_segment_keys

    def get_media_segment_key(self, uri):
        if uri in self._media_segment_keys:
            return self._media_segment_keys[uri]

    def set_media_segment_key(self, uri, media_segment_key):
        self._media_segment_keys[uri] = media_segment_key

    def save(self):
        # only save if we have a lock
        if self._lock is None:
            return

        # update expire date
        self._expire_dt = DT.datetime.now() + DT.timedelta(minutes=30)

        # save
        try:
            file_name = _get_cache_file_name(self._user)
            _logger.debug('Saving cache file "{}"'.format(file_name))

            with open(file_name, 'wb') as f:
                pickle.dump(self, f)
        except:
            # ignore this failure: not the end of the world
            pass

    def release(self):
        if self._lock is None:
            return

        self.save()
        lock_file = self._lock.lock_file
        self._lock.release(force=True)
        self._lock = None
        _logger.debug('Cache lock file "{}" released'.format(lock_file))

    def __getstate__(self):
        # let's not save the lock file
        props = self.__dict__.copy()
        props['_lock'] = None

        return props


def _get_cache_dir():
    # lookup order:
    #
    #   1. $TOUTV3_CACHE_DIR
    #   2. on Linux:
    #        a) $XDG_CACHE_HOME/toutv3
    #        b) ~/.cache/toutv3
    #   3. $PWD/.toutv3-cache
    cache_subdir = 'toutv3'
    cache_dir = os.environ.get('TOUTV3_CACHE_DIR')

    if cache_dir is None:
        if platform.system() == 'Linux':
            # see <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>
            cache_dir = os.environ.get('XDG_CACHE_HOME')

            if cache_dir is None:
                # ~/.cache: pretty standard
                home = os.path.expanduser('~')
                cache_dir = os.path.join(home, '.cache')

            cache_dir = os.path.join(cache_dir, cache_subdir)

    if cache_dir is None:
        # local cache directory
        cache_dir = os.path.join(os.getcwd(), '.{}-cache'.format(cache_subdir))

    # make sure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)

    return cache_dir


_re_file_name_char = re.compile(r'[a-zA-Z0-9^&\'@{}[\],$=!#()%.+~_-]')


def _get_cache_base_name(user):
    # the base name is SAN-MD5 here, where SAN is the user name
    # sanitized for a file system name (helps to locate a specific
    # cache/lock file), and MD5 is the MD5 digest of the original user
    # name to account for collisions of SAN.
    san_user = ''

    for c in user:
        if _re_file_name_char.match(c):
            san_user += c

    md5 = hashlib.md5()
    md5.update(user.encode())

    return '{}-{}'.format(san_user, md5.hexdigest())


def _get_cache_file_name(user):
    file_name = '{}.cache'.format(_get_cache_base_name(user))

    return os.path.join(_get_cache_dir(), file_name)


def _get_file_lock(user):
    file_name = '{}.lock'.format(_get_cache_base_name(user))
    file_name = os.path.join(_get_cache_dir(), file_name)

    return filelock.FileLock(file_name)


def _load(user):
    _logger.debug('Trying to load cache for user "{}"'.format(user))

    try:
        lock = _get_file_lock(user)
    except:
        # no lock, no luck
        _logger.debug('Cannot get cache file lock object: using empty cache')
        return _Cache(user)

    # acquire cache lock
    try:
        # wait one second until timeout...
        lock.acquire(1)
    except filelock.Timeout:
        # cache is already locked: return empty cache (will not be saved)
        _logger.warn('Cache is locked by lock file "{}": using empty cache'.format(lock.lock_file))
        return _Cache(user)
    except Exception as e:
        # other exception: return empty cache (will not be saved)
        _logger.warn('Cannot acquire lock file "{}": {}'.format(lock.lock_file, e))
        return _Cache(user)

    _logger.debug('Cache lock file "{}" acquired'.format(lock.lock_file))

    try:
        cache_file_name = _get_cache_file_name(user)
    except:
        # no lock, no luck
        _logger.debug('Cannot get cache file name: using empty cache')
        lock.release(force=True)
        return _Cache(user)

    if not os.path.isfile(cache_file_name):
        # cache does not exist: return empty cache (will be created
        # once saved)
        _logger.debug('Cache file "{}" does not exist: using empty cache'.format(cache_file_name))
        return _Cache(user, lock)

    _logger.debug('Loading cache file "{}"'.format(cache_file_name))

    try:
        with open(cache_file_name, 'rb') as f:
            cache = pickle.load(f)
            cache.lock = lock
    except:
        # probably a malformed cache: overwrite with empty cache
        return _Cache(user, lock)

    if cache.is_expired:
        # cache is expired: restart with fresh cache
        _logger.debug('Cache is expired')
        cache = _Cache(user, lock)
    else:
        _logger.debug('Loaded cache file "{}":'.format(cache_file_name))
        _logger.debug('  {} cookies'.format(len(cache.cookies)))
        _logger.debug('  {} base headers'.format(len(cache.base_headers)))
        _logger.debug('  {} TOU.TV base headers'.format(len(cache.toutv_base_headers)))
        _logger.debug('  {} search show summaries'.format(len(cache.search_show_summaries)))
        _logger.debug('  {} section summaries'.format(len(cache.section_summaries)))
        _logger.debug('  {} shows'.format(len(cache.shows)))
        _logger.debug('  {} sections'.format(len(cache.sections)))
        _logger.debug('  {} presentation settings'.format(len(cache.pres_settings)))
        _logger.debug('  Logged in: {}'.format(cache.is_logged_in))
        _logger.debug('  Expires: {}'.format(cache.expire_dt))

    return cache
