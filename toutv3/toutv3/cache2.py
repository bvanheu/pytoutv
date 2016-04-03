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
from slugify import slugify
import requests.cookies
import datetime as DT
import platform
import filelock
import logging
import os.path
import pickle


_logger = logging.getLogger(__name__)


class _Cache:
    def __init__(self, user, lock=None):
        if lock is None:
            lock_info = 'without lock'
        else:
            lock_info = 'with lock file "{}"'.format(lock.lock_file)

        _logger.debug('Creating cache for user "{}" {}'.format(user, lock_info))
        self._user = user
        self._lock = lock
        self._expire_dt = None
        self._base_headers = {}
        self._toutv_base_headers = {}
        self._cookies = requests.cookies.RequestsCookieJar()
        self._pres_settings = {}
        self._is_logged_in = False
        self._shows = {}
        self._sections = {}
        self._search_show_summaries = []
        self._section_summaries = OrderedDict()
        self._user_infos = None

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

    @property
    def sections(self):
        return self._sections

    def get_show(self, url_name):
        if url_name in self._shows:
            return self._shows[url_name]

    def set_show(self, url_name, show):
        self._shows[url_name] = show

    def get_section(self, name):
        if name in self._sections:
            return self._sections[name]

    def set_section(self, section):
        self._sections[section.name] = section

    def save(self):
        # only save if we have a lock
        if self._lock is None:
            return

        _logger.debug('Saving cache for user "{}"'.format(self._user))

        # save lock here so we don't serialize it
        lock = self._lock
        self._lock = None

        # update expire date
        self._expire_dt = DT.datetime.now() + DT.timedelta(minutes=30)

        # save
        file_name = get_cache_file_name(self._user)

        try:
            with open(file_name, 'wb') as f:
                pickle.dump(self, f)
        except Exception as e:
            raise e
        finally:
            # restore saved lock
            self._lock = lock

    def release(self):
        if self._lock is None:
            return

        _logger.debug('Releasing cache lock file "{}"'.format(self._lock.lock_file))
        self.save()
        self._lock.release(force=True)
        self._lock = None

    def __getstate__(self):
        # let's not save the lock file
        props = self.__dict__.copy()
        props['_lock'] = None

        return props


def get_cache_dir():
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


def get_cache_file_name(user):
    file_name = '{}.cache'.format(slugify(user))

    return os.path.join(get_cache_dir(), file_name)


def _get_file_lock(user):
    file_name = '{}.lock'.format(slugify(user))
    file_name = os.path.join(get_cache_dir(), file_name)

    return filelock.FileLock(file_name)


def load(user):
    lock = _get_file_lock(user)
    _logger.debug('Trying to load cache for user "{}"'.format(user))

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
    cache_file_name = get_cache_file_name(user)

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
