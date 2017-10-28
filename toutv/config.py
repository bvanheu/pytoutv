# Copyright (c) 2012, Benjamin Vanheuverzwijn <bvanheu@gmail.com>
# Copyright (c) 2014, Philippe Proulx <eepp.ca>
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
# DISCLAIMED. IN NO EVENT SHALL Benjamin Vanheuverzwijn OR Philippe Proulx
# BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7'
HEADERS = {
    'User-Agent': USER_AGENT
}
TOUTV_PLAYLIST_URL = 'http://api.radio-canada.ca/validationMedia/v1/Validation.html'
TOUTV_AUTH_PLAYLIST_URL = 'https://services.radio-canada.ca/media/validation/v2/'
TOUTV_PLAYLIST_PARAMS = {
    'appCode': 'toutv',
    'deviceType': 'iphone4',
    'connectionType': 'wifi',
    'output': 'json'
}
TOUTV_JSON_URL_PREFIX = 'https://api.tou.tv/v1/toutvapiservice.svc/json/'
TOUTV_BASE_URL = 'https://ici.tou.tv'
EMISSION_THUMB_URL_TMPL = 'http://images.tou.tv/w_400,c_scale,r_5/v1/emissions/16x9/{}.jpg'

TOUTV_AUTH_CLIENT_ID = "d6f8e3b1-1f48-45d7-9e28-a25c4c514c60"
TOUTV_AUTH_SESSION_URL = "https://services.radio-canada.ca/auth/oauth/v2/authorize?response_type=token&client_id=%s&scope=media-drmt+oob+openid+profile+email+id.write+media-validation.read.privileged&state=authCode&redirect_uri=http://ici.tou.tv/profiling/callback" % TOUTV_AUTH_CLIENT_ID
TOUTV_AUTH_TOKEN_URL = "https://services.radio-canada.ca/auth/oauth/v2/authorize"
TOUTV_AUTH_LOGIN_URL = "https://services.radio-canada.ca/auth/oauth/v2/authorize/login"
TOUTV_AUTH_CONSENT_URL = "https://services.radio-canada.ca/auth/oauth/v2/authorize/consent"
TOUTV_AUTH_CLAIMS_URL = "https://services.radio-canada.ca/media/validation/v2/GetClaims?token={}"

TOUTV_AUTH_TOKEN_PATH = ".toutv_token"
