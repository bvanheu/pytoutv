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

import argparse
import distutils.version
import locale
import os
import sys
import time
import logging
import textwrap
import platform
import toutv.dl
import toutv.client
import toutv.cache
import toutv.config
from toutvcli import __version__
from toutvcli.progressbar import ProgressBar


class CliError(RuntimeError):
    pass


class App:
    QUALITY_MIN = 'MIN'
    QUALITY_AVG = 'AVERAGE'
    QUALITY_MAX = 'MAX'

    def __init__(self, args):
        self._argparser = self._build_argparser()
        self._args = args
        self._dl = None
        self._stop = False
        self._logger = logging.getLogger(__name__)

    def run(self):
        locale.setlocale(locale.LC_ALL, '')

        # Errors are catched here and a corresponding error code is
        # returned. The codes are:
        #
        #   * 0: all okay
        #   * 1: client error
        #   * 2: download error (cancelled, file exists, no space left, etc.)
        #   * 3: network error (timeout, bad HTTP request, etc.)
        #   * 10: bad argument
        #   * 100: unknown error
        if not self._args:
            self._argparser.print_help()
            return 10

        args = self._argparser.parse_args(self._args)
        self._verbose = args.verbose

        if 'no_cache' not in args:
            args.no_cache = False

        no_cache = args.no_cache_global or args.no_cache

        if self._verbose:
            logging.basicConfig(level=logging.DEBUG)

        if args.build_client:
            self._toutvclient = self._build_toutv_client(no_cache)

        try:
            args.func(args)
        except toutv.client.ClientError as e:
            print('Client error: {}'.format(e), file=sys.stderr)
            return 1
        except toutv.dl.CancelledByUserError as e:
            print('Download cancelled by user', file=sys.stderr)
            return 2
        except toutv.dl.FileExistsError as e:
            msg = 'Destination file exists (use -f to force)'
            print(msg, file=sys.stderr)
            return 2
        except toutv.dl.NoSpaceLeftError:
            print('No space left on device while downloading', file=sys.stderr)
            return 2
        except toutv.dl.DownloadError as e:
            print('Download error: {}'.format(e), file=sys.stderr)
            return 2
        except toutv.exceptions.RequestTimeoutError as e:
            tmpl = 'Timeout error ({} s for "{}")'
            print(tmpl.format(e.timeout, e.url), file=sys.stderr)
            return 3
        except toutv.exceptions.UnexpectedHttpStatusCodeError as e:
            tmpl = 'Bad HTTP status code ({}) for "{}"'
            print(tmpl.format(e.status_code, e.url), file=sys.stderr)
            return 3
        except toutv.exceptions.NetworkError as e:
            print('Network error: {}'.format(e), file=sys.stderr)
            return 3
        except CliError as e:
            print('Command line error: {}'.format(e), file=sys.stderr)
            return 1
        except Exception as e:
            print('Unknown exception: {}: {}'.format(type(e), e),
                  file=sys.stderr)
            return 100

        return 0

    def _handle_no_match_exception(self, e):
        print('Cannot find "{}"'.format(e.query))
        if not e.candidates:
            return
        if len(e.candidates) == 1:
            print('Did you mean "{}"?'.format(e.candidates[0]))
        else:
            print('Did you mean one of the following?\n')
            for candidate in e.candidates:
                print('  * {}'.format(candidate))

    def _build_argparser(self):
        p = argparse.ArgumentParser(description='TOU.TV command line client')
        sp = p.add_subparsers(dest='command', help='Commands help')

        # version
        p.add_argument('-n', '--no-cache', action='store_true',
                       dest='no_cache_global', help='Disable cache')
        p.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
        p.add_argument('-V', '--version', action='version',
                       version='%(prog)s v{}'.format(__version__))

        # list command
        pl = sp.add_parser('list',
                           help='List emissions or episodes of an emission')
        pl.add_argument('emission', action='store', nargs='?', type=str,
                        help='List all episodes of an emission')
        pl.add_argument('-a', '--all', action='store_true',
                        help='List emissions without episodes')
        pl.add_argument('-n', '--no-cache', action='store_true',
                        help=argparse.SUPPRESS)
        pl.set_defaults(func=self._command_list)
        pl.set_defaults(build_client=True)

        # info command
        pi = sp.add_parser('info',
                           help='Get emission or episode information')
        pi.add_argument('emission', action='store', type=str,
                        help='Emission name for which to get information')
        pi.add_argument('episode', action='store', nargs='?', type=str,
                        help='Episode name for which to get information')
        pi.add_argument('-n', '--no-cache', action='store_true',
                        help=argparse.SUPPRESS)
        pi.add_argument('-u', '--url', action='store_true',
                        help='Get episode information using a TOU.TV URL')
        pi.set_defaults(func=self._command_info)
        pi.set_defaults(build_client=True)

        # search command
        ps = sp.add_parser('search',
                           help='Search TOU.TV emissions or episodes')
        ps.add_argument('query', action='store', type=str,
                        help='Search query')
        ps.set_defaults(func=self._command_search)
        ps.set_defaults(build_client=True)

        # fetch command
        pf = sp.add_parser('fetch',
                           help='Fetch one or all episodes of an emission')
        quality_choices = [
            App.QUALITY_MIN,
            App.QUALITY_AVG,
            App.QUALITY_MAX
        ]
        pf.add_argument('emission', action='store', type=str,
                        help='Emission name to fetch')
        pf.add_argument('episode', action='store', nargs='?', type=str,
                        help='Episode name to fetch')
        pf.add_argument('-b', '--bitrate', action='store', type=int,
                        help='Video bitrate (default: use default quality)')
        pf.add_argument('-d', '--directory', action='store',
                        default=os.getcwd(),
                        help='Output directory (default: CWD)')
        pf.add_argument('-f', '--force', action='store_true',
                        help='Overwrite existing output file')
        pf.add_argument('-n', '--no-cache', action='store_true',
                        help=argparse.SUPPRESS)
        pf.add_argument('-q', '--quality', action='store',
                        default=App.QUALITY_AVG, choices=quality_choices,
                        help='Video quality (default: {})'.format(App.QUALITY_AVG))
        pf.add_argument('-u', '--url', action='store_true',
                        help='Fetch an episode using a TOU.TV URL')
        pf.set_defaults(func=self._command_fetch)
        pf.set_defaults(build_client=True)

        # clean command
        pc = sp.add_parser('clean', help='Clean temporary downloaded files')
        pc.add_argument('directory', action='store', nargs='?',
                        default=os.getcwd(),
                        help='Directory to clean (default: CWD)')
        pc.set_defaults(func=self._command_clean)
        pc.set_defaults(build_client=False)

        return p

    @staticmethod
    def _build_cache():
        cache_name = '.toutv_cache'
        cache_path = cache_name
        if platform.system() == 'Linux':
            try:
                cache_dir = os.environ['XDG_CACHE_DIR']
                xdg_cache_path = os.path.join(cache_dir, 'toutv')
                if not os.path.exists(xdg_cache_path):
                    os.makedirs(xdg_cache_path)
                cache_path = os.path.join(xdg_cache_path, cache_name)
            except KeyError:
                home_dir = os.environ['HOME']
                home_cache_path = os.path.join(home_dir, '.cache', 'toutv')
                if not os.path.exists(home_cache_path):
                    os.makedirs(home_cache_path)
                cache_path = os.path.join(home_cache_path, cache_name)
        cache = toutv.cache.ShelveCache(cache_path)

        return cache

    def _build_toutv_client(self, no_cache):
        if no_cache:
            cache = toutv.cache.EmptyCache()
        else:
            try:
                cache = App._build_cache()
            except:
                print('Warning: not using cache (multiple instances of toutv?)',
                      file=sys.stderr)
                cache = toutv.cache.EmptyCache()

        return toutv.client.Client(cache=cache)

    def _command_clean(self, args):
        # make sure we have to clean a directory
        if not os.path.isdir(args.directory):
            raise CliError('"{}" is not an existing directory'.format(args.directory))

        import glob

        tmpdl = glob.glob(os.path.join(args.directory, '.toutv-*.*'))
        tmpcomplete = glob.glob(os.path.join(args.directory, '*.ts.part'))

        for f in tmpdl + tmpcomplete:
            try:
                self._logger.debug('removing file "{}"'.format(f))
                os.remove(f)
            except Exception as e:
                # not the end of the world
                self._logger.warn('could not remove file "{}": {}'.format(f, e))

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
                                quality=quality, bitrate=bitrate,
                                overwrite=args.force)
            return

        if args.emission is not None and args.episode is None:
            self._fetch_emission_episodes_name(args.emission,
                                               output_dir=args.directory,
                                               quality=args.quality,
                                               bitrate=args.bitrate,
                                               overwrite=args.force)
        elif args.emission is not None and args.episode is not None:
            self._fetch_episode_name(args.emission, args.episode,
                                     output_dir=output_dir, quality=quality,
                                     bitrate=bitrate, overwrite=args.force)

    def _command_search(self, args):
        self._print_search_results(args.query)

    def _print_search_results(self, query):
        searchresult = self._toutvclient.search(query)

        modified_query = searchresult.get_modified_query()
        print('Effective query: {}\n'.format(modified_query))

        if not searchresult.get_results():
            print('No results')
            return

        for result in searchresult.get_results():
            if result.get_emission() is not None:
                emission = result.get_emission()
                print('Emission: {}  [{}]'.format(emission.get_title(),
                                                  emission.get_id()))

                if emission.get_description():
                    print('')
                    description = textwrap.wrap(emission.get_description(), 78)
                    for line in description:
                        print('  {}'.format(line))

            if result.get_episode() is not None:
                episode = result.get_episode()
                print('Episode: {}  [{}]'.format(episode.get_title(),
                                                 episode.get_id()))

                infos_lines = []

                air_date = episode.get_air_date()
                if air_date is not None:
                    line = '  * Air date: {}'.format(air_date)
                    infos_lines.append(line)

                emission_id = episode.get_emission_id()
                if emission_id is not None:
                    line = '  * Emission ID: {}'.format(emission_id)
                    infos_lines.append(line)

                if infos_lines:
                    print('')
                    for line in infos_lines:
                        print(line)

                if episode.get_description():
                    print('')
                    description = textwrap.wrap(episode.get_description(), 78)
                    for line in description:
                        print('  {}'.format(line))

            print('\n')

    def _print_list_emissions(self, all=False):
        if all:
            emissions = self._toutvclient.get_emissions()
        else:
            repertoire = self._toutvclient.get_page_repertoire()
            emissions = repertoire.get_emissions()

        emissions_keys = list(emissions.keys())

        def title_sort_func(ekey):
            return locale.strxfrm(emissions[ekey].get_title())

        emissions_keys.sort(key=title_sort_func)
        for ekey in emissions_keys:
            title = emissions[ekey].get_title()
            print('{} - {}'.format(ekey, title))

    def _print_list_episodes(self, emission):
        episodes = self._toutvclient.get_emission_episodes(emission)

        print('{}:\n'.format(emission.get_title()))
        if len(episodes) == 0:
            print('No available episodes')
            return

        for episode in App._sort_episodes(episodes):
            sae = episode.get_sae()
            title = episode.get_title()
            print('  * {} - {} - {}'.format(episode.Id, sae, title))

    def _print_list_episodes_name(self, emission_name):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._print_list_episodes(emission)

    def _print_info_emission(self, emission):
        inner = emission.get_country()
        if inner is None:
            inner = 'Unknown country'
        if emission.get_year() is not None:
            inner = '{}, {}'.format(inner, emission.get_year())
        print('{}  [{}]'.format(emission.get_title(), inner))

        if emission.get_description() is not None:
            print('')
            description = textwrap.wrap(emission.get_description(), 80)
            for line in description:
                print(line)

        infos_lines = []
        if emission.get_network() is not None:
            line = '  * Network: {}'.format(emission.get_network())
            infos_lines.append(line)
        removal_date = emission.get_removal_date()
        if removal_date is not None:
            line = '  * Removal date: {}'.format(removal_date)
            infos_lines.append(line)
        tags = emission.get_tags()
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
        qualities = episode.get_available_qualities()

        print(emission.get_title())
        print('{}  [{}]'.format(episode.get_title(), episode.get_sae()))

        if episode.get_description() is not None:
            print('')
            description = textwrap.wrap(episode.get_description(), 80)
            for line in description:
                print(line)

        infos_lines = []
        air_date = episode.get_air_date()
        if air_date is not None:
            line = '  * Air date: {}'.format(air_date)
            infos_lines.append(line)
        infos_lines.append('  * Available qualities:')
        for quality in qualities:
            bitrate = quality.bitrate // 1000

            xres = quality.xres or '?'
            yres = quality.yres or '?'

            resolution = '{}x{}'.format(xres, yres)
            line = '    * {} kbps ({})'.format(bitrate, resolution)
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
            epname = episode_name
            episode = self._toutvclient.get_episode_by_name(emission, epname)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._print_info_episode(episode)

    @staticmethod
    def _get_average_bitrate(qualities):
        mi = qualities[0].bitrate
        ma = qualities[-1].bitrate
        avg = (ma + mi) // 2
        closest = min(qualities, key=lambda q: abs(q.bitrate - avg))

        return closest.bitrate

    def _print_cur_pb(self, done_segments, done_bytes, force):
        if self._verbose:
            return

        cur_time = time.time()

        # ensure 100% is printed
        if done_segments == self._cur_segments_count:
            force = True

        if not force and (cur_time - self._last_pb_time < .2):
            return

        self._last_pb_time = cur_time
        bar = self._cur_pb.get_bar(done_segments, done_bytes)

        sys.stdout.write('\r{}'.format(bar))
        sys.stdout.flush()

    def _on_dl_start(self, filename, total_segments):
        self._cur_filename = filename
        self._cur_segments_count = total_segments
        self._cur_pb = ProgressBar(filename, total_segments)
        self._last_pb_time = time.time()
        self._print_cur_pb(0, 0, True)

    def _on_dl_progress_update(self, done_segments, done_bytes,
                               done_segments_bytes):
        if self._stop:
            return

        self._print_cur_pb(done_segments, done_bytes, False)

    def _fetch_episode(self, episode, output_dir, bitrate, quality, overwrite):
        # Get available bitrates for episode
        qualities = episode.get_available_qualities()

        # Choose bitrate
        if bitrate is None:
            if quality == App.QUALITY_MIN:
                bitrate = qualities[0].bitrate
            elif quality == App.QUALITY_MAX:
                bitrate = qualities[-1].bitrate
            elif quality == App.QUALITY_AVG:
                bitrate = App._get_average_bitrate(qualities)

        # Create downloader
        opu = self._on_dl_progress_update
        self._dl = toutv.dl.Downloader(episode, bitrate=bitrate,
                                       output_dir=output_dir,
                                       on_dl_start=self._on_dl_start,
                                       on_progress_update=opu,
                                       overwrite=overwrite)

        # Start download
        self._dl.download()

        # Finished
        self._dl = None

    def _fetch_episode_name(self, emission_name, episode_name, output_dir,
                            quality, bitrate, overwrite):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        try:
            epname = episode_name
            episode = self._toutvclient.get_episode_by_name(emission, epname)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._fetch_episode(episode, output_dir=output_dir, quality=quality,
                            bitrate=bitrate, overwrite=overwrite)

    def _fetch_emission_episodes(self, emission, output_dir, bitrate, quality,
                                 overwrite):
        episodes = self._toutvclient.get_emission_episodes(emission)

        if not episodes:
            title = emission.get_title()
            print('No episodes available for emission "{}"'.format(title))
            return

        for episode in App._sort_episodes(episodes):
            title = episode.get_title()

            if self._stop:
                raise toutv.dl.CancelledByUserError()
            try:
                self._fetch_episode(episode, output_dir, bitrate, quality,
                                    overwrite)
                sys.stdout.write('\n')
                sys.stdout.flush()
            except toutv.exceptions.RequestTimeoutError:
                tmpl = 'Error: cannot fetch "{}": request timeout'
                print(tmpl.format(title), file=sys.stderr)
            except toutv.exceptions.UnexpectedHttpStatusCodeError:
                tmpl = 'Error: cannot fetch "{}": unexpected HTTP status code'
                print(tmpl.format(title), file=sys.stderr)
            except toutv.exceptions.NetworkError as e:
                tmpl = 'Error: cannot fetch "{}": {}'
                print(tmpl.format(title, e), file=sys.stderr)
            except toutv.dl.FileExistsError as e:
                tmpl = 'Error: cannot fetch "{}": destination file exists'
                print(tmpl.format(title), file=sys.stderr)
            except toutv.dl.CancelledByUserError as e:
                raise e
            except toutv.dl.DownloadError as e:
                tmpl = 'Error: cannot fetch "{}": {}'
                print(tmpl.format(title, e), file=sys.stderr)
            except Exception as e:
                tmpl = 'Error: cannot fetch "{}": {}'
                print(tmpl.format(title, e), file=sys.stderr)

    def _fetch_emission_episodes_name(self, emission_name, output_dir, bitrate,
                                      quality, overwrite):
        try:
            emission = self._toutvclient.get_emission_by_name(emission_name)
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return

        self._fetch_emission_episodes(emission, output_dir, bitrate, quality,
                                      overwrite)

    @staticmethod
    def _sort_episodes(episodes):
        def episode_sort_func(episode):
            return distutils.version.LooseVersion(episode.get_sae())

        return sorted(episodes.values(), key=episode_sort_func)


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            print('Cancelled by user', file=sys.stderr)
            sys.exit(1)

        import signal
        signal.signal(signal.SIGINT, handler)


def run():
    app = App(sys.argv[1:])
    _register_sigint(app)

    return app.run()
