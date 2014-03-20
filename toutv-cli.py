#!/usr/bin/env python

# Copyright (c) 2012, Benjamin Vanheuverzwijn <bvanheu@gmail.com>
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
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import os
import sys
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse
import difflib
from Crypto.Cipher import AES
import struct
import textwrap
import re
import string
import platform

from toutv import client, cache, m3u8, progressbar

class TooManyMatchesException(Exception):
    def __init__(self, possibilities):
        self.possibilities = possibilities

class NoMatchException(Exception):
    def __init__(self, possibility):
        self.possibility = possibility

class ToutvConsoleApp():
    def __init__(self):
        self.argparse = self.build_argparser()
        self.toutvclient = self.build_toutvclient()

    def run(self):
        args = self.argparse.parse_args()
        args.func(args)

    def build_argparser(self):
        parser = argparse.ArgumentParser(description='Tou.tv console script')

        subparsers = parser.add_subparsers(dest="command", help='Sub-commands help')

        # list command
        parser_list = subparsers.add_parser('list', help='List emissions or episodes of an emission')
        parser_list.add_argument('emission', action="store", nargs="?", type=str, help='List all episodes of an emission')
        parser_list.add_argument('-a', '--all', action="store_true", help='List emissions without any episodes listed')
        parser_list.set_defaults(func=self.command_list)

        # info command
        parser_info = subparsers.add_parser('info', help='Get information about an emission or episode')
        parser_info.add_argument('emission', action="store", type=str, help='Get information about an emission. If used with -u, get information about the episode from the tou.tv URL')
        parser_info.add_argument('episode', action="store", nargs="?", type=str, help='Get information about an episode')
        parser_info.add_argument('-u', '--url', action="store_true", help='Get information about an episode from a tout.tv URL')
        parser_info.set_defaults(func=self.command_info)

        # fetch command
        parser_fetch = subparsers.add_parser('fetch', help='Fetch one or all episodes of an emission')
        parser_fetch.add_argument('-q', '--quality', action="store", default="AVERAGE", choices=["MIN", "AVERAGE", "MAX"], help='Specify the video quality (default: AVERAGE)')
        parser_fetch.add_argument('-b', '--bitrate', action="store", type=int, help='Specify the bitrate (default: fallback to AVERAGE quality)')
        parser_fetch.add_argument('-d', '--directory', action="store", default=os.getcwd(), help='Output directory (default: ' + os.getcwd() + '/<file>)')
        parser_fetch.add_argument('-u', '--url', action="store_true", help='Fetch an episode from a tout.tv URL')
        parser_fetch.add_argument('emission', action="store", type=str, help='Fetch all episodes of the provided emission. If used with -u, fetch the episode from the tou.tv URL')
        parser_fetch.add_argument('episode', action="store", nargs="?", type=str, help='Fetch the episode')
        parser_fetch.set_defaults(func=self.command_fetch)

        # search command
        parser_search = subparsers.add_parser('search', help='Search into toutv emission and episodes')
        parser_search.add_argument('query', action="store", type=str, help='Search query')
        parser_search.add_argument('-m', '--max', action="store", type=int, help='Maximum number of results (default: infinite)')
        parser_search.set_defaults(func=self.command_search)

        return parser

    def build_toutvclient(self):
        transport_impl = client.TransportJson()

        if platform.system() == 'Linux':
            try:
                if not os.path.exists(os.environ['XDG_CACHE_DIR'] + '/toutv'):
                    os.makedirs(os.environ['XDG_CACHE_DIR'] + '/toutv')
                cache_impl = cache.CacheShelve(
                    os.environ['XDG_CACHE_DIR'] + '/toutv/.toutv_cache')
            except KeyError:
                if not os.path.exists(
                    os.environ['HOME'] + '/.cache/toutv'):
                    os.makedirs(
                        os.environ['HOME'] + '/.cache/toutv')
                cache_impl = cache.CacheShelve(
                    os.environ['HOME'] + '/.cache/toutv/.toutv_cache')
        else:
            cache_impl = cache.CacheShelve(".toutv_cache")

        toutvclient = client.ToutvClient(transport_impl, cache_impl)

        return toutvclient

    def command_list(self, args):
        if args.emission:
            self.list_episodes(args.emission)
        else:
            self.list_emissions(args.all)

    def command_info(self, args):
        if args.url:
            url_result = self.get_episode_from_url(args.emission)
            if url_result is None: return
            (args.emission, args.episode) = url_result

        if args.episode:
            self.info_episode(args.emission, args.episode)
        else:
            self.info_emission(args.emission)

    def command_fetch(self, args):
        if args.url:
            url_result = self.get_episode_from_url(args.emission)
            if url_result is None: return
            (args.emission, args.episode) = url_result

        if args.emission and not args.episode:
            self.fetch_episodes(args.emission, args.directory, quality=args.quality, bitrate=args.bitrate)

        if args.emission and args.episode:
            self.fetch_episode(args.emission, args.episode, args.directory, quality=args.quality, bitrate=args.bitrate)

    def command_search(self, args):
        self.search(args.query)

    def search(self, query):
        searchresult = self.toutvclient.search_terms(query)

        print("Query:")
        if searchresult.ModifiedQuery != query:
            print("\t" + searchresult.ModifiedQuery + " (" + query + ")")
        else:
            print("\t" + searchresult.ModifiedQuery)

        print("Results:")
        if len(searchresult.Results) == 0:
                print("\tNo result found for " + query)
        else:
            for result in searchresult.Results:
                if result.Emission is not None:

                    print("\tEmission:")
                    print("\t\t" + result.Emission.Title)

                    if result.Emission.Description:
                        description = textwrap.wrap(result.Emission.Description, 100)
                        for line in description:
                            print("\t\t\t" + line)

                if result.Episode is not None:
                    print("\tEpisode:\n")

                    if result.Episode.CategoryId is not None:
                        print("\t\tEmission ID: " + str(result.Episode.CategoryId))

                    if result.Episode.Id is not None:
                        print("\t\tEpisode ID: " + str(result.Episode.Id))

                    print("\t\t" + result.Episode.Title + ":")
                    if result.Episode.Description:
                        description = textwrap.wrap(result.Episode.Description, 100)
                        for line in description:
                            print("\t\t\t" + line)

    def list_emissions(self, all=False):
        if all:
            emissions = self.toutvclient.get_emissions()
            for k in emissions:
                print(emissions[k].Title + " - " + str(emissions[k].Id))
        else:
            repertoire = self.toutvclient.get_page_repertoire()
            emissionrepertoires = repertoire["emissionrepertoire"]

            for k in sorted(emissionrepertoires, key=lambda er: emissionrepertoires[er].Titre):
                print(emissionrepertoires[k].Titre + " - " + str(emissionrepertoires[k].Id))

    def list_episodes(self, emission_name):
        try:
            emission = self.get_emission_by_name(emission_name)

            print("Title:")
            print("\t" + emission.Title)

            print("Episodes:")
            episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

            if len(episodes) == 0:
                print("\tNo episodes for the provided emission ("+emission.Title+")")
            else:
                for k in sorted(episodes, key=lambda e: episodes[e].SeasonAndEpisode):
                    print("\t" + episodes[k].SeasonAndEpisode + " - " + episodes[k].Title + " - " + str(episodes[k].Id))
        except NoMatchException as ex:
            print("Unable to find '" + emission_name + "'")
            print("Did you mean '" + ex.possibility + "' instead of '" + emission_name + "'?")
        except TooManyMatchesException as ex:
            print("Unable to find '" + emission_name + "'")
            print("Did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)

    def info_emission(self, emission_name):
        try:
            emission = self.get_emission_by_name(emission_name)

            print("Title: ")
            print("\t" + emission.Title + "\t(" + (emission.Country if emission.Country else "Pays inconnu") + (" - " + str(emission.Year) if emission.Year else "") + ")")

            print("Description:")
            if emission.Description:
                description = textwrap.wrap(emission.Description, 100)
                for line in description:
                    print("\t" + line)
            else:
                print("\tAucune description")

            print("Network:")
            if emission.Network:
                print("\t" + emission.Network)
            else:
                print("\tunknown")

            print("Will be removed:")
            if emission.DateRetraitOuEmbargo:
                if emission.DateRetraitOuEmbargo == "":
                    print("\t" + str(emission.DateRetraitOuEmbargo))
                else:
                    print("\tnot available")
            else:
                print("\tunknown")

            print("Tags: ")
            if emission.EstContenuJeunesse:
                print("jeune ")
            if emission.EstExclusiviteRogers:
                print("rogers ")
        except NoMatchException as ex:
            print("Unable to find '" + emission_name + "'")
            print("Did you mean '" + ex.possibility + "' instead of '" + emission_name + "'?")
        except TooManyMatchesException as ex:
            print("Unable to find '" + emission_name + "'")
            print("Did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)

    def info_episode(self, emission_name, episode_name):
        try:
            emission = self.get_emission_by_name(emission_name)
        except NoMatchException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean '" + ex.possibility + "' instead of '" + emission_name + "'?")
            return
        except TooManyMatchesException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)
            return

        try:
            episode = self.get_episode_by_name(emission.Id, episode_name)
        except NoMatchException as ex:
            print("Unable to find '" + episode_name + "'")
            print("Did you mean '" + ex.possibility + "' instead of '" + episode_name + "'?")
            return
        except TooManyMatchesException as ex:
            print("Unable to find '" + episode_name + "'")
            print("Did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)
            return

        print("Emission:")
        print("\t" + emission.Title)

        print("Title:")
        print("\t" + episode.Title + "\t(" + episode.SeasonAndEpisode + ")")

        print("Date aired:")
        print("\t" + episode.AirDateFormated)

        print("Description")
        if episode.Description:
            description = textwrap.wrap(episode.Description, 100)
            for line in description:
                print("\t" + line)
        else:
            print("No description")

        urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.LWPCookieJar())))

        url = self.toutvclient.fetch_playlist_url(episode.PID)

        request = urllib.request.Request(url, None, {"User-Agent" : client.IPHONE4_USER_AGENT})
        m3u8_file = urllib.request.urlopen(request).read().decode('utf-8')

        playlist = m3u8.parse(m3u8_file, os.path.dirname(url))

        bitrates = self.get_video_bitrates(playlist)

        print("Available bitrate:")
        for bitrate in bitrates:
            print("\t" + str(bitrate) + " bit/s")

    def fetch_episodes(self, emission_name, directory, quality="AVERAGE", bitrate=0):
        try:
            emission = self.get_emission_by_name(emission_name)
        except NoMatchException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean '" + ex.possibility + "' instead of '" + emission_name + "'?")
            return
        except TooManyMatchesException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)
            return

        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

        if len(episodes):
            print("Fetching " + str(len(episodes)) + " episodes from " +  emission_name)
            for episode_id, episode in sorted(episodes.items()):
                self.fetch_episode(emission_name, episode.Title, directory, quality, bitrate)
        else:
            print("No episodes available for " + emission_name)

    def fetch_episode(self, emission_name, episode_name, directory, quality="AVERAGE", bitrate=0):
        try:
            emission = self.get_emission_by_name(emission_name)
        except NoMatchException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean '" + ex.possibility + "' instead of '" + emission_name + "'?")
            return
        except TooManyMatchesException as ex:
            print("unable to find '" + emission_name + "'")
            print("did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)
            return

        try:
            episode = self.get_episode_by_name(emission.Id, episode_name)
        except NoMatchException as ex:
            print("Unable to find '" + episode_name + "'")
            print("Did you mean '" + ex.possibility + "' instead of '" + episode_name + "'?")
            return
        except TooManyMatchesException as ex:
            print("Unable to find '" + episode_name + "'")
            print("Did you mean one of the following?")
            for possibility in ex.possibilities:
                print("\t" + possibility)
            return

        print("Emission and episode:")
        print("\t" + emission.Title + " - " + episode.Title + "\t(" + episode.SeasonAndEpisode + ")")

        urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.LWPCookieJar())))

        url = self.toutvclient.fetch_playlist_url(episode.PID)
        request = urllib.request.Request(url, None, {"User-Agent" : client.IPHONE4_USER_AGENT})
        m3u8_file = urllib.request.urlopen(request).read().decode('utf-8')


        playlist = m3u8.parse(m3u8_file, os.path.dirname(url))

        # Stream bandwidth selection
        bitrates = self.get_video_bitrates(playlist)

        stream = None
        if bitrate:
            if bitrate in bitrates:
                stream = self.get_video_stream_for_bitrate(playlist, bitrate)
            else:
                print("warning: " + str(bitrate) + " not in " + str(bitrates) + ", fallback to AVERAGE quality")

        if stream is None:
            stream = self.get_video_stream_for_quality(playlist, quality)

        print("Fetching video with bitrate " + str(stream.bandwidth) + " bit/s")

        request = urllib.request.Request(stream.uri, None, {'User-Agent': client.IPHONE4_USER_AGENT} )
        m3u8_file = urllib.request.urlopen(request).read().decode('utf-8')


        playlist = m3u8.parse(m3u8_file, os.path.dirname(stream.uri))

        request = urllib.request.Request(playlist.segments[0].key.uri, None, {'User-Agent': client.IPHONE4_USER_AGENT})
        key = urllib.request.urlopen(request).read()


        # Output file handling
        if directory is None:
            directory = os.getcwd()

        if not os.path.exists(os.path.expanduser(directory)):
            os.mkdir(os.path.expanduser(directory))

        # Remove illegal chars from filename
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = emission.Title + "-" + episode.Title + ".ts"
        filename = ''.join(c for c in filename if c in valid_chars)

        sys.stdout.write("Downloading " + str(len(playlist.segments)) + " segments...\n")
        sys.stdout.flush()
        progress_bar = progressbar.ProgressBar(0, len(playlist.segments), mode='fixed')
        output_file = open(os.path.join(os.path.expanduser(directory), filename), "wb")
        count = 1
        for segment in playlist.segments:
            request = urllib.request.Request(segment.uri, None, {'User-Agent' : client.IPHONE4_USER_AGENT})
            ts_file = urllib.request.urlopen(request).read()

            aes = AES.new(key, AES.MODE_CBC, struct.pack(">IIII", 0x0, 0x0, 0x0, count))

            output_file.write(aes.decrypt(ts_file))

            count += 1

            progress_bar.increment_amount()
            sys.stdout.write(str(progress_bar) + '\r')
            sys.stdout.flush()

        sys.stdout.write("\n")
        sys.stdout.flush()

        output_file.close()

        return None

    def get_video_bitrates(self, playlist):
        bitrates = []
        for stream in playlist.streams:
            index = os.path.basename(stream.uri)
            # Toutv team doesnt use the "AUDIO" or "VIDEO" m3u8 tag so we must parse the URL to find out about video stream
            # index_X_av.m3u8 -> audio-video (av)
            # index_X_a.m3u8 -> audio (a)
            if index.split("_", 2)[2][0:2] == "av":
                bitrates.append(stream.bandwidth)

        return bitrates

    def get_video_stream_for_bitrate(self, playlist, bitrate):
        bitrates = self.get_video_bitrates(playlist)

        if bitrate in bitrates:
            for stream in playlist.streams:
                if stream.bandwidth == bitrate:
                    return stream

        return 0

    def get_video_stream_for_quality(self, playlist, quality):
        bitrates = self.get_video_bitrates(playlist)

        if quality == "MIN":
            bandwidth = min(bitrates, key=int)
        elif quality == "MAX":
            bandwidth = max(bitrates, key=int)
        else:
            # AVERAGE
            bandwidth = bitrates[((len(bitrates)+1)/2 if len(bitrates)%2 else len(bitrates)/2)]

        for stream in playlist.streams:
            if stream.bandwidth == bandwidth:
                return stream

    def get_emission_by_name(self, emission_name):
        emissions = self.toutvclient.get_emissions()
        emission_name_upper = emission_name.upper()

        possibilities = []
        for emission_id, emission in emissions.items():
            possibilities.append(str(emission.Id))
            # Store titles in uppercase for case-insensitive comparisons.
            possibilities.append(str(emission.Title.upper()))

        close_matches = difflib.get_close_matches(emission_name_upper, possibilities)

        # Not an exact match...
        if close_matches[0] != emission_name_upper:
            # Unable to find exactly 1 match... i dunno wat to do
            if len(close_matches) > 1:
                raise TooManyMatchesException(close_matches)

            raise NoMatchException(close_matches[0])

        # Got an exact match
        for emission_id, emission in emissions.items():
            if emission_name_upper in [str(emission.Id), emission.Title.upper()]:
                return emission

        raise Exception("unable to find " + emission_name)

    def get_episode_by_name(self, emission_id, episode_name):
        episodes = self.toutvclient.get_episodes_for_emission(emission_id)
        episode_name_upper = episode_name.upper()

        possibilities = []
        for episode_id, episode in episodes.items():
            possibilities.append(str(episode.Id))
            possibilities.append(str(episode.Title.upper()))
            possibilities.append(str(episode.SeasonAndEpisode))

        close_matches = difflib.get_close_matches(episode_name_upper, possibilities)

        if len(close_matches) == 0:
            raise NoMatchException("")

        # Not an exact match...
        if close_matches[0] != episode_name_upper:
            # Unable to find 1 match... i dunno wat to do
            if len(close_matches) > 1:
                raise TooManyMatchesException(close_matches)

            raise NoMatchException(close_matches[0])

        # Got an exact match
        for episode_id, episode in episodes.items():
            if episode_name_upper in [str(episode.Id), episode.Title.upper(), episode.SeasonAndEpisode]:
                return episode

        raise Exception("unable to find " + episode_name)

    def get_episode_from_url(self, url):
        try:
            response = urllib.request.urlopen(url)

            #extract emission and episode id from meta tag
            found = re.search('<meta +content="([^".]+)\\.([^"]+)" +name="ProfilingEmisodeToken" +/>', response.read().decode('utf-8'))
            if found is None:
                print('Cannot find episode information in %s' % response.url)
            else:
                return found.groups()
        except urllib.error.HTTPError as ex:
            print('Cannot open %s: %d %s' % (ex.url, ex.code, ex.reason))
        except IOError as ex:
            print('Cannot open %s: %s' % (url, ex.reason))

#
# _/~MAIN~\_
#
if __name__ == "__main__":
    app = ToutvConsoleApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("quitting...")

    sys.exit(0)
