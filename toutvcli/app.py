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
import getpass
import re
import toutv.dl
import toutv.client
import toutv.cache
import toutv.config
import toutv.auth
import toutv.exceptions
from toutvcli import __version__
from toutvcli.progressbar import ProgressBar
import traceback
from urllib.parse import urlparse


class CliError(RuntimeError):
    pass


class App:
    QUALITY_MIN = 'MIN'
    QUALITY_AVG = 'AVERAGE'
    QUALITY_MAX = 'MAX'

    FETCH_INFO_FIRST_ARG = 'show-or-url'
    FETCH_INFO_SECOND_ARG = 'episode'

    def __init__(self, args):
        self._argparser = self._build_argparser()
        self._args = args
        self._dl = None
        self._stop = False
        self._logger = logging.getLogger(__name__)
        self._toutv_client = None
        self._verbose = False
        self._quiet = False

    def run(self):
        locale.setlocale(locale.LC_ALL, '')

        # Errors are caught here and a corresponding error code is
        # returned. The codes are:
        #
        #   * 0: all okay
        #   * 1: client error
        #   * 2: download error (cancelled, file exists, no space left, etc.)
        #   * 3: network error (timeout, bad HTTP request, etc.)
        #   * 100: unknown error

        args = self._argparser.parse_args(self._args)

        self._verbose = args.verbose

        if 'quiet' in args:
            if args.quiet:
                self._quiet = True
            elif not sys.__stdin__.isatty():
                print("Non-interactive shell; enabling --quiet")
                self._quiet = True

        if 'no_cache' not in args:
            args.no_cache = False

        no_cache = args.no_cache_global or args.no_cache

        if self._verbose:
            logging.basicConfig(level=logging.DEBUG)

        if args.build_client:
            self._toutv_client = self._build_toutv_client(no_cache)

        try:
            args.func(args)
        except toutv.client.ClientError as e:
            print('Client error: {}'.format(e), file=sys.stderr)
            return 1
        except toutv.dl.CancelledByUserError:
            print('Download cancelled by user', file=sys.stderr)
            return 2
        except toutv.dl.FileExistsError as e:
            tmpl = 'Destination file {} exists (use -f to overwrite).'
            print(tmpl.format(e.path), file=sys.stderr)
            return 2
        except toutv.dl.NoSpaceLeftError:
            print('No space left on device while downloading', file=sys.stderr)
            return 2
        except toutv.dl.DownloadError as e:
            print('Download error: {}'.format(e), file=sys.stderr)

            if self._verbose:
                traceback.print_exc()

            return 2
        except toutv.exceptions.RequestTimeoutError as e:
            tmpl = 'Timeout error ({} s for "{}")'
            print(tmpl.format(e.timeout, e.url), file=sys.stderr)
            return 3
        except toutv.exceptions.UnexpectedHttpStatusCodeError as e:
            tmpl = 'Bad HTTP status code ({}) for "{}"'
            if e.status_code == 401 and os.path.exists(App._build_cache_path(toutv.config.TOUTV_AUTH_TOKEN_PATH)):
                print("Invalid auth token; will be deleted. You will need to run 'toutv login [email_address]' to resolve this issue.", file=sys.stderr)
                App._delete_auth()
                return run()
            print(tmpl.format(e.status_code, e.url), file=sys.stderr)
            return 3
        except toutv.exceptions.NetworkError as e:
            print('Network error: {}'.format(e), file=sys.stderr)
            return 3
        except CliError as e:
            print('Command line error: {}'.format(e), file=sys.stderr)
            return 1
        except toutv.client.NoMatchException as e:
            self._handle_no_match_exception(e)
            return 1
        except Exception as e:
            print('Unknown exception: {}: {}'.format(type(e), e),
                  file=sys.stderr)

            if self._verbose:
                traceback.print_exc()

            return 100

        return 0

    @staticmethod
    def _handle_no_match_exception(e):
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
        sp.required = True

        # version
        p.add_argument('-n', '--no-cache', action='store_true',
                       dest='no_cache_global', help='Disable cache')
        p.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
        p.add_argument('-V', '--version', action='version',
                       version='%(prog)s v{}'.format(__version__))

        # list command
        usage = ('\n\n'
                 '    1. toutv list [options]\n'
                 '    2. toutv list [options] <show>\n')

        desc = '''
List shows (1) or episodes of a show (2).  In form 2, the show can be specified
using its name, url or id (as found with the form 1 of this command).
'''
        pl = sp.add_parser('list',
                           help='List shows or episodes of a show',
                           usage=usage, description=desc)
        pl.add_argument('show', action='store', nargs='?', type=str,
                        help='Name or url of a show')
        pl.add_argument('-n', '--no-cache', action='store_true',
                        help=argparse.SUPPRESS)
        pl.set_defaults(func=self._command_list)
        pl.set_defaults(build_client=True)

        # info command
        usage = ('\n\n'
                 '    1. toutv info [options] <show-url>\n'
                 '    2. toutv info [options] <episode-url>\n'
                 '    3. toutv info [options] <show>\n'
                 '    4. toutv info [options] <show> <episode>\n')

        desc = '''
Print some information about a show (1 and 3) or an episode (2 and 4). In forms
3 and 4, shows can be referred to using the name or the id as found with the
list command. Episodes can be specified using their name, number or id.
'''

        pi = sp.add_parser('info',
                           help='Get information about a show or an episode',
                           usage=usage, description=desc)
        pi.add_argument(App.FETCH_INFO_FIRST_ARG, action='store', type=str,
                        help='Show or URL, depending on the form used.')
        pi.add_argument(App.FETCH_INFO_SECOND_ARG, action='store', nargs='?', type=str,
                        help='Episode, if necessary.')
        pi.add_argument('-n', '--no-cache', action='store_true',
                        help=argparse.SUPPRESS)
        pi.set_defaults(func=self._command_info)
        pi.set_defaults(build_client=True)

        # search command
        ps = sp.add_parser('search',
                           help='Search TOU.TV shows or episodes')
        ps.add_argument('query', action='store', type=str,
                        help='Search query')
        ps.set_defaults(func=self._command_search)
        ps.set_defaults(build_client=True)

        # fetch command
        usage = ('\n\n'
                 '    1. toutv fetch [options] <episode-url>\n'
                 '    2. toutv fetch [options] <show-url>\n'
                 '    3. toutv fetch [options] <show> <episode>\n'
                 '    4. toutv fetch [options] <show>\n')

        desc = '''
Fetch an episode (1 and 3) or all episodes of a show (2 and 4). In forms 3 and
4, shows can be referred to using the name or the id as found with the list
command. The episode can be specified using its name, number or id.
'''

        pf = sp.add_parser('fetch',
                           help='Fetch one or all episodes of a show',
                           usage=usage, description=desc)
        quality_choices = [
            App.QUALITY_MIN,
            App.QUALITY_AVG,
            App.QUALITY_MAX
        ]
        pf.add_argument(App.FETCH_INFO_FIRST_ARG, action='store', type=str,
                        help='Show or URL, depending on the form used.')
        pf.add_argument(App.FETCH_INFO_SECOND_ARG, action='store', type=str, nargs='?',
                        help='Episode, if necessary.')
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
        pf.add_argument('-Q', '--quiet', action='store_true',
                        help='Don\'t show progress while downloading')
        pf.set_defaults(func=self._command_fetch)
        pf.set_defaults(build_client=True)

        # clean command
        pc = sp.add_parser('clean', help='Clean temporary downloaded files')
        pc.add_argument('directory', action='store', nargs='?',
                        default=os.getcwd(),
                        help='Directory to clean (default: CWD)')
        pc.set_defaults(func=self._command_clean)
        pc.set_defaults(build_client=False)

        # login command
        pn = sp.add_parser('login', help='Login to have access to extra content')
        pn.add_argument('username', action='store', type=str,
                        help='Tou.tv user email')
        pn.add_argument('password', action='store', nargs='?', type=str,
                        help='Tou.tv user password')
        pn.set_defaults(func=self._command_login)
        pn.set_defaults(build_client=False)

        return p

    @staticmethod
    def _build_cache_path(cache_name):
        cache_path = cache_name
        if platform.system() in ['Linux', 'Darwin']:
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
        elif platform.system() == 'Windows':
            if 'APPDATA' in os.environ:
                cache_dir = os.environ['APPDATA']
                appdata_cache_path = os.path.join(cache_dir, 'toutv')
                if not os.path.exists(appdata_cache_path):
                    os.makedirs(appdata_cache_path)
                cache_path = os.path.join(appdata_cache_path, cache_name)

        return cache_path

    @staticmethod
    def _build_cache():
        return toutv.cache.ShelveCache(App._build_cache_path('.toutv_cache'))

    @staticmethod
    def _build_auth():
        auth = None

        try:
            with open(App._build_cache_path(toutv.config.TOUTV_AUTH_TOKEN_PATH), 'r') as token_file:
                auth = toutv.auth.Auth(token_file.read())
        except Exception:
            pass

        return auth

    @staticmethod
    def _delete_auth():
        token_file = App._build_cache_path(toutv.config.TOUTV_AUTH_TOKEN_PATH)
        os.remove(token_file)

    def _build_toutv_client(self, no_cache):
        auth = App._build_auth()

        if no_cache:
            cache = toutv.cache.EmptyCache()
        else:
            try:
                cache = App._build_cache()
            except Exception:
                print('Warning: not using cache (multiple instances of toutv?)',
                      file=sys.stderr)

                if self._verbose:
                    traceback.print_exc()

                cache = toutv.cache.EmptyCache()

        return toutv.client.Client(cache=cache, auth=auth)

    def _parse_show_episode_from_args(self, first, second):
        # Parse the arguments used to specify a show or an episode. If first is
        # an URL, we extract the show name and episode number (if applicable)
        # from it.  If not, we consider that first and second are keywords
        # (name, number or id) describing respectively the show and the
        # episode, so they are returned as-is.  No validation (e.g. check if
        # the show/episode exists) is done on the keywords.
        #
        # Here are examples of allowed forms to refer to an episode:
        #
        #   - "http://ici.tou.tv/district-31/S01E56", None
        #   - "District 31", "S01E56"
        #   - "District 31", "Épisode 56"
        #   - "district-31" "S01E56"
        #   - "2424967431" "2425170307"
        #
        #   or to a show:
        #   - "http://ici.tou.tv/district-31", None
        #   - "district-31", None

        # Try to parse the first argument as an URL, this will tell us if we use the URL form or the keyword form.
        url = urlparse(first)

        if url.scheme in ('http', 'https'):
            # It's an URL, so check that there is no extra argument.
            if second is not None:
                raise CliError('A single argument must be passed when using the URL form.')

            # Validate that the URL is using the right domain.
            if url.netloc != 'ici.tou.tv':
                raise CliError('URL from unrecognized domain {}'.format(url.netloc))

            # Cleanup and split the path part (e.g. path='/district-31/S01E56')
            elements = url.path.strip('/').split('/')

            # Validate the number of path elements.
            if len(elements) not in [1, 2] or len(elements[0]) == 0:
                raise CliError('Couldn\'t recognize URL {}'.format(first))

            show_spec = elements[0]
            episode_spec = elements[1] if len(elements) == 2 else None
        else:
            show_spec = first
            episode_spec = second

        if self._verbose:
            tpl = '_parse_show_episode_from_args returns: emission {} and episode {}'
            print(tpl.format(show_spec, episode_spec))

        return show_spec, episode_spec

    def _get_show_episode_from_args(self, first, second):
        # Get the show and episode objects referred to by first and second.
        # See doc of _parse_show_episode_from_args for the acceptable values.
        show_spec, episode_spec = self._parse_show_episode_from_args(first, second)

        show = self._toutv_client.get_emission_by_whatever(show_spec)

        if episode_spec:
            episode = self._toutv_client.get_episode_by_name(show, episode_spec)
        else:
            episode = None

        return show, episode

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
                self._logger.warning('could not remove file "{}": {}'.format(f, e))

    @staticmethod
    def _command_login(args):
        auth = toutv.auth.Auth()

        password = args.password
        if password is None:
            password = getpass.getpass()

        try:
            auth.login(args.username, password)
            token = auth.get_token()

            print('Login successful')
            print('Token: {}'.format(token))

            with open(App._build_cache_path(toutv.config.TOUTV_AUTH_TOKEN_PATH), 'w') as token_file:
                token_file.write(token)
        except Exception as e:
            print('Unable to login "{}"'.format(e))

    def _command_list(self, args):
        if args.show:
            # List episodes of a show.
            show, episode = self._get_show_episode_from_args(args.show, None)

            if episode:
                raise CliError("Episode URL given to the list command.")

            self._print_list_episodes(show)
        else:
            # List shows.
            self._print_list_emissions()

    def _command_info(self, args):
        first = getattr(args, App.FETCH_INFO_FIRST_ARG)
        second = getattr(args, App.FETCH_INFO_SECOND_ARG)

        show, episode = self._get_show_episode_from_args(first, second)

        if episode:
            self._print_info_episode(episode)
        else:
            self._print_info_emission(show)

    def _command_fetch(self, args):
        output_dir = args.directory
        bitrate = args.bitrate
        quality = args.quality
        overwrite = args.force

        first = getattr(args, App.FETCH_INFO_FIRST_ARG)
        second = getattr(args, App.FETCH_INFO_SECOND_ARG)

        show, episode = self._get_show_episode_from_args(first, second)

        if episode:
            self._fetch_episode(episode, output_dir=output_dir, quality=quality, bitrate=bitrate, overwrite=overwrite)
        else:
            self._fetch_emission_episodes(show, output_dir=output_dir, quality=quality, bitrate=bitrate,
                                          overwrite=overwrite)

    def _command_search(self, args):
        self._print_search_results(args.query)

    def _print_search_results(self, query):
        searchresult = self._toutv_client.search(query)

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

    def _print_list_emissions(self):
        shows = self._toutv_client.get_emissions()

        def title_sort_func(show):
            return locale.strxfrm(show.get_title())

        for show in sorted(shows, key=title_sort_func):
            title = show.get_title()
            print('{} - {}'.format(show.get_id(), title))

    def _print_list_episodes(self, emission):
        episodes = self._toutv_client.get_emission_episodes(emission, True)

        print('{}:\n'.format(emission.get_title()))
        if len(episodes) == 0:
            print('No available episodes')
            return

        for episode in App._sort_episodes(episodes):
            sae = episode.get_sae()
            title = episode.get_title()
            date = episode.get_air_date()
            print('  * {} - {} - {}'.format(sae, title, date))

    def _print_info_emission(self, emission):
        if emission.get_description() is None:
            url = '{}/presentation{}'.format(toutv.config.TOUTV_BASE_URL, emission.Url)
            emission_dto = self._toutv_client._transport._do_query_json_url(url, {'v': 2, 'excludeLineups': True, 'd': 'android'})
            emission.Description = emission_dto['Details']['Description']
            emission.Country = emission_dto['Details']['Country']

        inner = emission.get_country()
        if inner is None:
            inner = 'Unknown country'
        if emission.get_year() is not None:
            inner = '{}, {}'.format(inner, emission.get_year())
        print('{}  [{}]'.format(emission.get_title(), inner))
        print('ID: {}'.format(emission.get_id()))

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

    @staticmethod
    def _print_info_episode(episode):
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

    def _on_dl_start(self, total_segments):
        self._cur_segments_count = total_segments
        self._cur_pb = ProgressBar(self._seg_handler.filename, total_segments)
        self._last_pb_time = time.time()
        if self._quiet:
            print("Downloading {} ... ".format(self._seg_handler.filename), end="", flush=True)
        else:
            self._print_cur_pb(0, 0, True)

    def _on_dl_progress_update(self, num_completed_segments,
                               num_bytes_completed_segments,
                               num_bytes_partial_segment):
        if self._stop:
            return
        if self._quiet:
            return

        total_bytes = num_bytes_completed_segments + num_bytes_partial_segment
        self._print_cur_pb(num_completed_segments, total_bytes, False)

    @staticmethod
    def _get_fetch_filename_for_episode(episode, quality_level):
        emission_title = episode.get_emission().Title
        episode_title = episode.Title

        if episode.SeasonAndEpisode is not None:
            sae = episode.SeasonAndEpisode
            episode_title = '{} {}'.format(sae, episode_title)

        episode_title = '{}.{}'.format(episode_title, quality_level)
        filename = '{}.{}.ts'.format(emission_title, episode_title)

        # remove illegal characters from filename
        regex = r'[^ \'a-zA-Z0-9áàâäéèêëíìîïóòôöúùûüÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜçÇ()._-]'
        filename = re.sub(regex, '', filename)
        filename = re.sub(r'\s', '.', filename)

        return filename

    def _fetch_episode(self, episode, output_dir, bitrate, quality, overwrite):
        # Get available bitrates for episode
        qualities = episode.get_available_qualities()

        quality_level = "qAVG"
        # Choose bitrate
        if bitrate is None:
            if quality == App.QUALITY_MIN:
                bitrate = qualities[0].bitrate
                quality_level = "qMIN"
            elif quality == App.QUALITY_MAX:
                bitrate = qualities[-1].bitrate
                quality_level = "qMAX"
            elif quality == App.QUALITY_AVG:
                bitrate = App._get_average_bitrate(qualities)

        filename = App._get_fetch_filename_for_episode(episode, quality_level)

        # Create segment handler
        self._seg_handler = toutv.dl.FilesystemSegmentHandler(
            episode=episode, bitrate=bitrate, output_dir=output_dir, filename=filename,
            overwrite=overwrite)

        seg_provider = toutv.dl.ToutvApiSegmentProvider(
            episode=episode, bitrate=bitrate)

        # Create downloader
        self._dl = toutv.dl.Downloader(
            seg_provider=seg_provider,
            seg_handler=self._seg_handler,
            on_progress_update=self._on_dl_progress_update,
            on_dl_start=self._on_dl_start)

        # Start download
        self._dl.download()

        # Finished
        self._dl = None
        if self._quiet:
            print("Done.")

    def _fetch_emission_episodes(self, emission, output_dir, bitrate, quality, overwrite):
        episodes = self._toutv_client.get_emission_episodes(emission, True)

        if not episodes:
            title = emission.get_title()
            print('No episodes available for emission "{}"'.format(title))
            return

        for episode in App._sort_episodes(episodes):
            title = episode.get_title()

            try:
                if self._stop:
                    raise toutv.dl.CancelledByUserError()
                if episode.PID is None:
                    episode = self._toutv_client.get_episode_by_name(emission, str(episode.Id))
                self._fetch_episode(episode, output_dir, bitrate, quality, overwrite)
                sys.stdout.write('\n')
                sys.stdout.flush()
            except toutv.exceptions.RequestTimeoutError:
                tmpl = 'Error: cannot fetch "{}": request timeout'
                print(tmpl.format(title), file=sys.stderr)
            except toutv.exceptions.UnexpectedHttpStatusCodeError:
                tmpl = 'Error: cannot fetch "{}": unexpected HTTP status code'
                print(tmpl.format(title), file=sys.stderr)
            except toutv.exceptions.NetworkError as e:
                tmpl = 'Error: cannot fetch "{}": NetworkError - {}'
                print(tmpl.format(title, e), file=sys.stderr)
            except toutv.dl.FileExistsError as e:
                tmpl = 'Error: cannot fetch "{}": destination file {} already exists'
                print(tmpl.format(title, e.path), file=sys.stderr)
            except toutv.dl.CancelledByUserError as e:
                raise e
            except toutv.dl.DownloadError as e:
                tmpl = 'Error: cannot fetch "{}": DownloadError - {}'
                print(tmpl.format(title, e), file=sys.stderr)
            except Exception as e:
                tmpl = 'Error: cannot fetch "{}": {}'
                print(tmpl.format(title, e), file=sys.stderr)
                if self._verbose:
                    traceback.print_exc()

    @staticmethod
    def _sort_episodes(episodes):
        def episode_sort_func(episode):
            return distutils.version.LooseVersion(episode.get_sae())

        return sorted(episodes, key=episode_sort_func)


def _register_sigint():
    if platform.system() == 'Linux':
        def handler(signal, frame):
            print('Cancelled by user', file=sys.stderr)
            sys.exit(1)

        import signal
        signal.signal(signal.SIGINT, handler)


def run():
    app = App(sys.argv[1:])
    _register_sigint()

    return app.run()


if __name__ == '__main__':
    run()
