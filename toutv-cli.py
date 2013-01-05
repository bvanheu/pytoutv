#!/usr/bin/env python2

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
import cookielib
import urllib2
from Crypto.Cipher import AES
import struct
import textwrap

from toutv import client, cache, m3u8, progressbar

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
        parser_list.add_argument('emission', action="store", nargs="?", type=int, help='List all episodes of an emission')
        parser_list.add_argument('-a', '--all', action="store_true", help='List emissions without any episodes listed')
        parser_list.set_defaults(func=self.command_list)

        # info command
        parser_info = subparsers.add_parser('info', help='Get information about an emission or episode')
        parser_info.add_argument('emission', action="store", type=int, help='Get information about an emission')
        parser_info.add_argument('episode', action="store", nargs="?", type=int, help='Get information about an episode')
        parser_info.set_defaults(func=self.command_info)

        # fetch command
        parser_fetch = subparsers.add_parser('fetch', help='Fetch one or all episodes of an emission')
        parser_fetch.add_argument('emission', action="store", type=int, help='Fetch all episodes of the provided emission')
        parser_fetch.add_argument('episode', action="store", nargs="?", type=int, help='Fetch the episode')
        parser_fetch.add_argument('-q', '--quality', action="store", default="AVERAGE", choices=["MIN", "AVERAGE", "MAX"], help='Specify the video quality (default: AVERAGE)')
        parser_fetch.add_argument('-b', '--bitrate', action="store", type=int, help='Specify the bitrate (default: fallback to AVERAGE quality)')
        parser_fetch.add_argument('-d', '--directory', action="store", default=os.getcwd(), help='Output directory (default: ' + os.getcwd() + '/<file>)')
        parser_fetch.set_defaults(func=self.command_fetch)

        # search command
        parser_search = subparsers.add_parser('search', help='Search into toutv emission and episodes')
        parser_search.add_argument('query', action="store", type=str, help='Search query')
        parser_search.add_argument('-m', '--max', action="store", type=int, help='Maximum number of results (default: infinite)')
        parser_search.set_defaults(func=self.command_search)

        return parser

    def build_toutvclient(self):
        transport_impl = client.TransportJson()
        cache_impl = cache.CacheShelve(".toutv_cache")

        toutvclient = client.ToutvClient(transport_impl, cache_impl)

        return toutvclient

    def command_list(self, args):
        if args.emission:
            self.list_episodes(args.emission)
        else:
            self.list_emissions(args.all)

    def command_info(self, args):
        if args.episode:
            self.info_episode(args.emission, args.episode)
        else:
            self.info_emission(args.emission)

    def command_fetch(self, args):
        self.fetch_episodes(args.emission, args.episode, args.directory, quality=args.quality, bitrate=args.bitrate)

    def command_search(self, args):
        self.search(' '.join(args.query))

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
                    print("\tEpisode:")
                    print("\t\t" + result.Episode.Title)
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

    def list_episodes(self, emission_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        print("Title:")
        print("\t" + emission.Title)

        print("Episodes:")
        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

        if len(episodes) == 0:
            print("\tNo episodes for the provided emission ("+emission.Title+")")
        else:
            for k in sorted(episodes, key=lambda e: episodes[e].SeasonAndEpisode):
                print("\t" + episodes[k].SeasonAndEpisode + " - " + episodes[k].Title + " - " + str(episodes[k].Id))

    def info_emission(self, emission_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

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

        print "Tags: ",
        if emission.EstContenuJeunesse:
            print "jeune ",
        if emission.EstExclusiviteRogers:
            print "rogers "

    def info_episode(self, emission_id, episode_id):
        emissions = self.toutvclient.get_emissions()
        emission = emissions[emission_id]

        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

        if episode_id not in episodes:
            print("This episode does not exist.");
            return

        episode = episodes[episode_id]

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

        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())))

        url = self.toutvclient.fetch_playlist_url(episode.PID)

        request = urllib2.Request(url, None, {"User-Agent" : client.IPHONE4_USER_AGENT})
        m3u8_file = urllib2.urlopen(request).read()

        m3u8_parser = m3u8.M3u8_Parser()

        playlist = m3u8_parser.parse(m3u8_file, os.path.dirname(url))

        bitrates = self.get_video_bitrate(playlist)

        print("Available bitrate:")
        for bitrate in bitrates:
            print("\t" + str(bitrate) + " bit/s")

    def fetch_episodes(self, emission_id, episode_id, directory, quality="AVERAGE", bitrate=0):
        emissions = self.toutvclient.get_emissions()

        if emission_id not in emissions:
            print("Show " + str(emission_id) + " does not exist.")
            return

        emission = emissions[emission_id]

        episodes = self.toutvclient.get_episodes_for_emission(emission.Id)

        if episode_id not in episodes:
            print("This episode does not exist");
            return

        episode = episodes[episode_id]

        print("Emission and episode:")
        print("\t" + emission.Title + " - " + episode.Title + "\t(" + episode.SeasonAndEpisode + ")")

        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.LWPCookieJar())))

        url = self.toutvclient.fetch_playlist_url(episode.PID)

        request = urllib2.Request(url, None, {"User-Agent" : client.IPHONE4_USER_AGENT})
        m3u8_file = urllib2.urlopen(request).read()

        m3u8_parser = m3u8.M3u8_Parser()

        playlist = m3u8_parser.parse(m3u8_file, os.path.dirname(url))

        # Stream bandwidth selection
        bitrates = self.get_video_bitrate(playlist)

        stream = None
        if bitrate:
            if bitrate in bitrates:
                stream = self.get_video_stream_for_bitrate(playlist, bitrate)
            else:
                print("warning: " + str(bitrate) + " not in " + str(bitrates) + ", fallback to AVERAGE quality")

        if stream is None:
            stream = self.get_video_stream_for_quality(playlist, quality)

        print("Fetching video with bitrate " + str(stream.bandwidth) + " bit/s")

        request = urllib2.Request(stream.uri, None, {'User-Agent': client.IPHONE4_USER_AGENT} )
        m3u8_file = urllib2.urlopen(request).read()

        playlist = m3u8_parser.parse(m3u8_file, os.path.dirname(stream.uri))

        request = urllib2.Request(playlist.segments[0].key.uri, None, {'User-Agent': client.IPHONE4_USER_AGENT})
        key = urllib2.urlopen(request).read()

        # Output file handling
        if directory is None:
            directory = os.getcwd()

        if not os.path.exists(os.path.expanduser(directory)):
            os.mkdir(os.path.expanduser(directory))

        sys.stdout.write("Downloading " + str(len(playlist.segments)) + " segments...\n")
        sys.stdout.flush()
        progress_bar = progressbar.ProgressBar(0, len(playlist.segments), mode='fixed')
        output_file = open(os.path.join(os.path.expanduser(directory), emission.Title + "-" + episode.Title + ".ts"), "w")
        count = 1
        for segment in playlist.segments:
            request = urllib2.Request(segment.uri, None, {'User-Agent' : client.IPHONE4_USER_AGENT})
            ts_file = urllib2.urlopen(request).read()

            aes = AES.new(key, AES.MODE_CBC, struct.pack(">IIII", 0x0, 0x0, 0x0, count))

            output_file.write(aes.decrypt(ts_file))

            count += 1

            progress_bar.increment_amount()
            print progress_bar, '\r',
            sys.stdout.flush()

        sys.stdout.write("\n")
        sys.stdout.flush()

        output_file.close()

        return None

    def get_video_bitrate(self, playlist):
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
        bitrates = self.get_video_bitrate(playlist)

        if bitrate in bitrates:
            for stream in playlist.streams:
                if stream.bandwidth == bitrate:
                    return stream

        return 0

    def get_video_stream_for_quality(self, playlist, quality):
        bitrates = self.get_video_bitrate(playlist)

        if quality == "MIN":
            bandwidth = min(bitrates, key=int)
        elif quality == "MAX":
            bandwidth = max(bitrates, key=int)
        else:
            # AVERAGE
            bandwidth =  bitrates[((len(bitrates)+1)/2 if len(bitrates)%2 else len(bitrates)/2)]

        for stream in playlist.streams:
            if stream.bandwidth == bandwidth:
                return stream

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
