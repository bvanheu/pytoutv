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
import textwrap
import platform
import toutv.dl
import toutv.client
import toutv.cache
import toutv.config
import toutv.dl
from toutv import m3u8
from toutvcli.progressbar import ProgressBar


class App:
    def __init__(self, args):
        self._argparser = self._build_argparser()
        self._toutvclient = self._build_toutv_client()
        self._args = args
        self._dl = None
        self._stop = False

    def run(self):
        args = self._argparser.parse_args(self._args)

        try:
            args.func(args)
        except toutv.client.ClientError as e:
            sys.stderr.write('Error: {}\n'.format(e))
            return 1
        except toutv.dl.DownloaderError as e:
            sys.stderr.write('Download error: {}\n'.format(e))
            return 2
        except toutv.dl.CancelledException as e:
            sys.stderr.write('\nDownload cancelled by user\n'.format(e))
            return 3
        except Exception as e:
            sys.stderr.write('Unknown error: {}\n'.format(e))
            return 4

        return 0

    def stop(self):
        if self._dl is not None:
            self._dl.cancel()
        self._stop = True

    def _handle_no_match_exception(self, e):
        print('Cannot find "{}"'.format(e.query))
        if not e.candidates:
            return
        if len(e.candidates) == 1:
            print('Did you mean "{}"?'.format(e.candidates[0]))
        else:
            print('Did you mean one of the following?')
            for candidate in e.candidates:
                print('  * {}'.format(candidate))

    def _build_argparser(self):
        p = argparse.ArgumentParser(description='TOU.TV command line client')
        sp = p.add_subparsers(dest='command', help='Commands help')

        # list command
        pl = sp.add_parser('list',
                           help='List emissions or episodes of an emission')
        pl.add_argument('emission', action='store', nargs='?', type=str,
                        help='List all episodes of an emission')
        pl.add_argument('-a', '--all', action='store_true',
                        help='List emissions without episodes')
        pl.set_defaults(func=self._command_list)

        # info command
        pi = sp.add_parser('info',
                           help='Get emission or episode information')
        pi.add_argument('emission', action='store', type=str,
                        help='Emission name for which to get information')
        pi.add_argument('episode', action='store', nargs='?', type=str,
                        help='Episode name for which to get information')
        pi.add_argument('-u', '--url', action='store_true',
                        help='Get episode information using a TOU.TV URL')
        pi.set_defaults(func=self._command_info)

        # fetch command
        pf = sp.add_parser('fetch',
                           help='Fetch one or all episodes of an emission')
        pf.add_argument('-q', '--quality', action='store', default='AVERAGE',
                        choices=['MIN', 'AVERAGE', 'MAX'],
                        help='Video quality (default: AVERAGE)')
        pf.add_argument('-b', '--bitrate', action='store', type=int,
                        help='Video bitrate (default: fallback to AVERAGE quality)')
        pf.add_argument('-d', '--directory', action='store',
                        default=os.getcwd(),
                        help='Output directory (default: CWD)')
        pf.add_argument('-u', '--url', action='store_true',
                        help='Fetch an episode using a TOU.TV URL')
        pf.add_argument('emission', action='store', type=str,
                        help='Emission name to fetch')
        pf.add_argument('episode', action='store', nargs='?', type=str,
                        help='Episode name to fetch')
        pf.set_defaults(func=self._command_fetch)

        # search command
        ps = sp.add_parser('search',
                           help='Search TOU.TV emissions or episodes')
        ps.add_argument('query', action='store', type=str,
                        help='Search query')
        ps.set_defaults(func=self._command_search)

        return p

    def _build_toutv_client(self):
        cache_name = '.toutv_cache'
        cache_path = cache_name
        if platform.system() == 'Linux':
            try:
                xdg_cache_path = os.path.join(os.environ['XDG_CACHE_DIR'],
                                              'toutv')
                if not os.path.exists(xdg_cache_path):
                    os.makedirs(xdg_cache_path)
                cache_path = os.path.join(xdg_cache_path, cache_name)
            except KeyError:
                home_cache_path = os.path.join(os.environ['HOME'], '.cache',
                                               'toutv')
                if not os.path.exists(home_cache_path):
                    os.makedirs(home_cache_path)
                cache_path = os.path.join(home_cache_path, cache_name)
        cache = toutv.cache.ShelveCache(cache_path)

        return toutv.client.Client(cache=cache)

    def _command_list(self, args):
        if args.emission:
            self._print_list_episodes_name(args.emission)
        else:
            self._print_list_emissions(args.all)

    def _command_info(self, args):
        if args.url:
            em = args.emission
            episode = self._toutvclient.get_episode_from_url(em)
            self._print_info_episode(episode)
            return

        if args.episode:
            self._print_info_episode_name(args.emission, args.episode)
        else:
            self._print_info_emission_name(args.emission)

    def _command_fetch(self, args):
        output_dir = args.directory
        bitrate = args.bitrate
        quality = args.quality

        if args.url:
            em = args.emission
            episode = self._toutvclient.get_episode_from_url(em)
            self._fetch_episode(episode, output_dir=output_dir,
                                quality=quality, bitrate=bitrate)
            return

        if args.emission and not args.episode:
            self._fetch_emission_episodes_name(args.emission,
                                               output_dir=args.directory,
                                               quality=args.quality,
                                               bitrate=args.bitrate)

        if args.emission and args.episode:
            self._fetch_episode_name(args.emission, args.episode,
                                     output_dir=output_dir, quality=quality,
                                     bitrate=bitrate)

    def _command_search(self, args):
        self._print_search_results(args.query)

    def _print_search_results(self, query):
        searchresult = self._toutvclient.search(query)

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

    def _print_list_emissions(self, all=False):
        if all:
            emissions = self._toutvclient.get_emissions()
            emissions_keys = list(emissions.keys())
            title_func = lambda ekey: emissions[ekey].Title
            id_func = lambda ekey: ekey
        else:
            repertoire = self._toutvclient.get_page_repertoire()
            repertoire_emissions = repertoire.Emissions
            emissions_keys = list(repertoire_emissions.keys())
            title_func = lambda ekey: repertoire_emissions[ekey].Titre
            id_func = lambda ekey: ekey

        emissions_keys.sort(key=title_func)
        for ekey in emissions_keys:
            emid = id_func(ekey)
            title = title_func(ekey)
            print('{}: {}'.format(emid, title))

    def _print_list_episodes(self, emission):
        episodes = self._toutvclient.get_emission_episodes(emission)

        print('{}:\n'.format(emission.Title))
        if len(episodes) == 0:
            print('No available episodes')
            return

        key_func = lambda key: episodes[key].SeasonAndEpisode
        episodes_keys = list(episodes.keys())
        episodes_keys.sort(key=key_func)
        for ekey in episodes_keys:
            episode = episodes[ekey]
            sae = episode.SeasonAndEpisode
            title = episode.Title
            print('  * {}: {} {}'.format(ekey, sae, title))

    def _print_list_episodes_name(self, emission_name):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._print_list_episodes(emission)

    def _print_info_emission(self, emission):
        inner = emission.Country
        if inner is None:
            inner = 'Unknown country'
        if emission.Year is not None:
            inner = '{}, {}'.format(inner, emission.Year)
        print('{}  [{}]'.format(emission.Title, inner))

        if emission.Description is not None:
            print('')
            description = textwrap.wrap(emission.Description, 78)
            for line in description:
                print(line)

        infos_lines = []
        if emission.Network is not None:
            line = '  * Network: {}'.format(emission.Network)
            infos_lines.append(line)
        removal_date = emission.get_removal_date()
        if removal_date is not None:
            line = '  * Removal date: {}'.format(removal_date)
            infos_lines.append(line)
        tags = []
        if emission.EstContenuJeunesse is not None:
            tags.append('jeunesse')
        if emission.EstExclusiviteRogers is not None:
            tags.append('rogers')
        if tags:
            tags_list = ', '.join(tags)
            line = '  * Tags: {}'.format(tags_list)
            infos_lines.append(line)

        if infos_lines:
            print('\n\nInfos:\n')
            for line in infos_lines:
                print(line)

    def _print_info_emission_name(self, emission_name):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._print_info_emission(emission)

    def _print_info_episode(self, episode):
        emission = episode.get_emission()
        bitrates = episode.get_available_bitrates()

        print(emission.Title)
        print('{}  [{}]'.format(episode.Title, episode.SeasonAndEpisode))

        if episode.Description is not None:
            print('')
            description = textwrap.wrap(episode.Description, 78)
            for line in description:
                print(line)

        infos_lines = []
        air_date = episode.get_air_date()
        if air_date is not None:
            line = '  * Air date: {}'.format(air_date)
            infos_lines.append(line)
        infos_lines.append('  * Available bitrates:')
        for bitrate in bitrates:
            bitrate = bitrate // 1000
            line = '    * {} kbps'.format(bitrate)
            infos_lines.append(line)

        print('\n\nInfos:\n')
        for line in infos_lines:
            print(line)

    def _print_info_episode_name(self, emission_name, episode_name):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        try:
            episode = self._toutvclient.get_episode_by_name(emission, episode_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._print_info_episode(episode)

    @staticmethod
    def _get_average_bitrate(bitrates):
        mi = bitrates[0]
        ma = bitrates[-1]
        avg = (ma + mi) // 2
        closest = min(bitrates, key=lambda x: abs(x - avg))

        return closest

    def _print_cur_pb(self, total_segments, total_bytes):
        bar = self._cur_pb.get_bar(total_segments, total_bytes)
        sys.stdout.write('\r{}'.format(bar))
        sys.stdout.flush()

    def _on_dl_start(self, filename, segments_count):
        self._cur_filename = filename
        self._cur_segments_count = segments_count
        self._cur_pb = ProgressBar(filename, segments_count)
        self._print_cur_pb(0, 0)

    def _on_dl_progress_update(self, total_segments, total_bytes):
        self._print_cur_pb(total_segments, total_bytes)

    def _fetch_episode(self, episode, output_dir, bitrate, quality):
        # Get available bitrates for episode
        bitrates = episode.get_available_bitrates()

        # Choose bitrate
        if bitrate is None:
            if quality == 'MIN':
                bitrate = bitrates[0]
            elif quality == 'MAX':
                bitrate = bitrates[-1]
            elif quality == 'AVERAGE':
                bitrate = App._get_average_bitrate(bitrates)

        # Create downloader
        opu = self._on_dl_progress_update
        self._dl = toutv.dl.Downloader(episode, bitrate=bitrate,
                                       output_dir=output_dir,
                                       on_dl_start=self._on_dl_start,
                                       on_progress_update=opu)

        # Start download
        self._dl.download()

        # Finished
        self._dl = None

    def _fetch_episode_name(self, emission_name, episode_name, output_dir,
                            quality='AVERAGE', bitrate=0):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        try:
            episode = self._toutvclient.get_episode_by_name(emission, episode_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._fetch_episode(episode, output_dir=output_dir, quality=quality,
                            bitrate=bitrate)

    def _fetch_emission_episodes(self, emission, output_dir, bitrate, quality):
        episodes = self._toutvclient.get_emission_episodes(emission)

        if not episodes:
            print('No episodes available for emission "{}"'.format(emission.Title))
            return

        for episode in episodes.values():
            if self._stop:
                raise toutv.dl.CancelledException()
            try:
                self._fetch_episode(episode, output_dir, bitrate, quality)
                sys.stdout.write('\n')
                sys.stdout.flush()
            except toutv.dl.CancelledException as e:
                raise e
            except:
                title = episode.Title
                sys.stderr.write('Error: cannot fetch "{}"\n'.format(title))

    def _fetch_emission_episodes_name(self, emission_name, output_dir, bitrate,
                                      quality='AVERAGE'):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._fetch_emission_episodes(emission, output_dir, bitrate, quality)


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            app.stop()

        import signal
        signal.signal(signal.SIGINT, handler)


def run(args):
    app = App(args)
    _register_sigint(app)

    return app.run()
