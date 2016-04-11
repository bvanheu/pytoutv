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

from toutv3 import agent
import logging


_logger = logging.getLogger(__name__)


class Client:
    """
    TOU.TV client.

    This is the main entry point of the :ref:`API <API>`.
    """

    def __init__(self, user, password, no_cache=False):
        """
        Creates a TOU.TV client, logging in with user name *user*
        and password *password*.

        If *no_cache* is ``True``, then no :ref:`cache <cache>`
        is created/loaded.
        """

        self._user = user
        self._password = password
        self._agent = agent._Agent(user, password, no_cache)

    @property
    def user_infos(self):
        """
        :py:class:`toutv3.model.UserInfos` object containing the
        informations and profile of the client's user.
        """

        return self._agent.get_user_infos()

    @property
    def search_show_summaries(self):
        """
        List of :py:class:`toutv3.model.SearchShowSummary` objects.
        """

        return self._agent.get_search_show_summaries()

    @property
    def section_summaries(self):
        """
        Dictionary mapping section names to
        :py:class:`toutv3.model.SectionSummary` objects.
        """

        return self._agent.get_section_summaries()

    def get_show(self, url_name):
        """
        Returns a :py:class:`toutv3.model.Show` object correspoding to
        the URL name *url_name*.

        The URL name of a show can be found in the
        :py:attr:`toutv3.model.SearchShowSummary.url` or
        :py:attr:`toutv3.model.ShowLineupItem.url` property.
        """
        return self._agent.get_show(url_name)

    def get_section(self, name):
        """
        Returns a :py:class:`toutv3.model.Section` object correspoding to
        the section name *name*.
        """
        return self._agent.get_section(name)

    def release_cache(self):
        """
        Releases the :ref:`cache <cache>` created/loaded by this
        client, if any.
        """

        self._agent.release_cache()
