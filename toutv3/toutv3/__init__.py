__version__ = '3.0.0-dev'


class Error(Exception):
    pass


class NetworkError(Error):
    pass


class HttpError(NetworkError):
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
        return self._method

    @property
    def url(self):
        return self._url

    @property
    def data(self):
        return self._data

    @property
    def headers(self):
        return self._headers

    @property
    def params(self):
        return self._params

    @property
    def allow_redirects(self):
        return self._allow_redirects


class NetworkTimeout(HttpError):
    pass


class ConnectionError(HttpError):
    pass


class UnexpectedHttpStatusCode(HttpError):
    def __init__(self, status_code, *args):
        super().__init__(*args)
        self._status_code = status_code

    @property
    def status_code(self):
        return self._status_code


class InvalidCredentials(Error):
    def __init__(self, user, password):
        self._user = user
        self._password = password

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password


class ApiChanged(Error):
    pass


class DownloadError(Error):
    pass


class CancelledByUser(DownloadError):
    pass


class FileExists(DownloadError):
    pass


class NoSpaceLeft(DownloadError):
    pass
