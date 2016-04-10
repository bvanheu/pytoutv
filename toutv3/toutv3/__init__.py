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

__version__ = '3.0.0-dev'


class Error(Exception):
    """
    Generic error.
    """
    pass


class NetworkError(Error):
    """
    Generic network error.
    """
    pass


class HttpError(NetworkError):
    """
    HTTP error.

    The properties of this object describe the HTTP request at the
    origin of this error.
    """

    def __init__(self, method, url, data, headers, params, allow_redirects):
        super().__init__()
        self._method = method
        self._url = url
        self._data = data
        self._headers = headers
        self._params = params
        self._allow_redirects = allow_redirects

    @property
    def method(self):
        """
        HTTP method (``GET`` or ``POST``).
        """

        return self._method

    @property
    def url(self):
        """
        HTTP URL.
        """

        return self._url

    @property
    def data(self):
        """
        HTTP POST data (:py:class:`dict` or ``None``).
        """

        return self._data

    @property
    def headers(self):
        """
        HTTP headers (:py:class:`dict` or ``None``).
        """

        return self._headers

    @property
    def params(self):
        """
        Additional HTTP URL parameters (:py:class:`dict` or ``None``).
        """

        return self._params

    @property
    def allow_redirects(self):
        """
        ``True`` if redirects were allowed.
        """

        return self._allow_redirects


class NetworkTimeout(HttpError):
    """
    Network timeout error.
    """

    pass


class ConnectionError(HttpError):
    """
    Network connection error.
    """

    pass


class UnexpectedHttpStatusCode(HttpError):
    """
    Unexpected status in HTTP response.
    """

    def __init__(self, status_code, *args):
        super().__init__(*args)
        self._status_code = status_code

    @property
    def status_code(self):
        """
        Unexpected HTTP status (integer).
        """
        return self._status_code


class InvalidCredentials(Error):
    """
    Invalid credentials when trying to connect to TOU.TV.
    """

    def __init__(self, user, password):
        self._user = user
        self._password = password

    @property
    def user(self):
        """
        User name that was tried.
        """

        return self._user

    @property
    def password(self):
        """
        Password that was tried.
        """

        return self._password


class ApiChanged(Error):
    """
    TOU.TV API seems to have changed error.

    This is raised when the code expects a response formatted in a
    specific way from the TOU.TV API, but it gets something else, or
    an invalid HTTP response.
    """

    pass


class UnsupportedMedia(Error):
    """
    Unsupported media error.

    This is usually raised when a download of DRM-protected contents
    was requested.
    """

    pass


class DownloadError(Error):
    """
    Generic download error.
    """

    def __init__(self, download, msg):
        super().__init__(msg)
        self._download = download

    @property
    def download(self):
        """
        Download object (:py:class:`toutv3.download.Download`) at the
        origin of this error.
        """

        return self._download


class NoSpaceLeft(DownloadError):
    """
    No space left on device error.
    """

    def __init__(self, download, msg):
        super().__init__(download, msg)
