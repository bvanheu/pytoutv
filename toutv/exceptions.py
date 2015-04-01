# Copyright (c) 2014, Philippe Proulx <eepp.ca>
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


class NetworkError(RuntimeError):

    def __str__(self):
        return 'Network error'


class RequestTimeoutError(NetworkError):

    def __init__(self, url, timeout):
        self._url = url
        self._timeout = timeout

    @property
    def url(self):
        return self._url

    @property
    def timeout(self):
        return self._timeout

    def __str__(self):
        tmpl = 'Request timeout ({} s for "{}")'
        return tmpl.format(self._timeout, self._url)


class UnexpectedHttpStatusCodeError(NetworkError):

    def __init__(self, url, status_code):
        self._url = url
        self._status_code = status_code

    @property
    def url(self):
        return self._url

    @property
    def status_code(self):
        return self._status_code

    def __str__(self):
        tmpl = 'Unexpected HTTP response code {} for "{}"'
        return tmpl.format(self._status_code, self._url)
