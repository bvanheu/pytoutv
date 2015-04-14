from nctoutv.ui import _MainFrame, _PopUpLauncher
import toutv.client
import toutv.cache
import threading
import argparse
import platform
import logging
import nctoutv
import signal
import urwid
import queue
import sys
import os


class _Request:
    pass


class _GetShowsRequest(_Request):
    pass


class _GetEpisodesRequest(_Request):
    def __init__(self, show):
        self.show = show


class _Response:
    def __init__(self, request):
        self.request = request


class _GetShowsResponse(_Response):
    def __init__(self, request, shows):
        self.shows = shows
        super().__init__(request)


class _GetEpisodesResponse(_Response):
    def __init__(self, request, episodes):
        self.episodes = episodes
        super().__init__(request)


def _get_cache():
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


def _get_client(no_cache):
    if no_cache:
        cache = toutv.cache.EmptyCache()
    else:
        try:
            cache = _get_cache()
        except:
            cache = toutv.cache.EmptyCache()

    return toutv.client.Client(cache=cache)


def _request_thread(app, request_queue, no_cache):
    logger = logging.getLogger('{}.{}'.format(__name__, '_request_thread'))

    def process_get_shows(request):
        shows = client.get_page_repertoire().get_emissions()

        return _GetShowsResponse(request, shows)

    def process_get_episodes(request):
        show = request.show
        episodes = client.get_emission_episodes(show)

        return _GetEpisodesResponse(request, episodes)

    client = _get_client(no_cache)
    rq_cb = {
        _GetShowsRequest: process_get_shows,
        _GetEpisodesRequest: process_get_episodes,
    }

    while True:
        request = request_queue.get()
        logger.debug('got request {}'.format(request))
        response = rq_cb[type(request)](request)
        logger.debug('sending response {}'.format(response))
        app.handle_response(response)


class _App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow,bold', 'dark blue'),
        ('header-key', 'white,bold', 'dark blue'),
        ('footer', 'black', 'dark green'),
        ('footer-not-found', 'light red,bold', 'dark green'),
        ('selected-item', 'default,standout', ''),
        ('current-show', 'white,bold', 'dark cyan'),
        ('search-result', 'yellow', ''),
        ('search-result-invalid', 'dark red', ''),
        ('show-title', 'default,bold', ''),
        ('key', 'default,bold', ''),
        ('sae', 'default,bold', ''),
        ('sae-selected', 'default,bold,standout', ''),
        ('show-info-title', 'light blue,bold', ''),
        ('show-info', 'default,bold', ''),
    ]

    def __init__(self):
        self._response_handlers = {
            _GetShowsResponse: self._handle_get_shows_response,
            _GetEpisodesResponse: self._handle_get_episodes_response,
        }

    def _build_main_frame(self):
        self._main_frame = _MainFrame(self)

    def _build_popup_launcher(self):
        self._popup_launcher = _PopUpLauncher(self._main_frame)

    def _create_loop(self):
        self._loop = urwid.MainLoop(widget=self._popup_launcher,
                                    palette=_App._palette,
                                    unhandled_input=self._unhandled_input,
                                    handle_mouse=False, pop_ups=True)

    def _handle_get_shows_response(self, response):
        self._main_frame.set_shows(response.shows)
        self.set_status_msg_okay()

    def _handle_get_episodes_response(self, response):
        self._main_frame.set_episodes(response.episodes, response.request.show)
        self._main_frame.set_current_show(response.request.show)
        self._main_frame.focus_episodes()
        self.set_status_msg_okay()

    def _rt_wp_cb(self, unused=None):
        self._response_handlers[type(self._last_response)](self._last_response)
        self._request_sent = False

    def _create_client_thread(self):
        self._logger.debug('creating client thread')
        self._rt_wp = self._loop.watch_pipe(self._rt_wp_cb)
        self._rt_queue = queue.Queue()
        args = [self, self._rt_queue, self._args.no_cache]
        self._rt = threading.Thread(target=_request_thread, args=args,
                                    daemon=True)
        self._request_sent = False
        self._rt.start()

    def _unhandled_input(self, key):
        if key in ('q', 'Q', 'esc'):
            self._do_exit()

    def _create_exit_pipe(self):
        self._exit_pipe = self._loop.watch_pipe(self._do_exit)

    def _do_exit(self, _=None):
        self._logger.info('quitting')
        raise urwid.ExitMainLoop()

    def request_exit(self):
        os.write(self._exit_pipe, b'boom')
        print("done")

    def set_status_msg(self, msg):
        self._main_frame.set_status_msg(msg)

    def set_status_msg_okay(self):
        self._main_frame.set_status_msg_okay()

    def show_episodes(self, show):
        self._send_get_episodes_request(show)

    def focus_shows(self):
        self._main_frame.focus_shows()

    def handle_response(self, response):
        self._logger.debug('handling response {}'.format(response))
        self._last_response = response
        os.write(self._rt_wp, 'lol'.encode())

    def show_show_info(self, show):
        self._main_frame.show_show_info(show)

    def _send_request(self, request):
        if not self._request_sent:
            self._request_sent = True
            self._rt_queue.put(request)
            self._logger.debug('request sent ({})'.format(request))

            return True

        return False

    def _send_get_shows_request(self):
        self._logger.debug('sending "get shows" request')
        self._send_request(_GetShowsRequest())

    def _send_get_episodes_request(self, show):
        self._logger.debug('sending "get episodes" request for show: {}'.format(show))

        if self._send_request(_GetEpisodesRequest(show)):
            self._main_frame.set_episodes_info_loading(show)
            fmt = 'Loading episodes of {}...'
            self.set_status_msg(fmt.format(show.get_title()))

    def _parse_args(self):
        p = argparse.ArgumentParser(description='TOU.TV TUI client')
        p.add_argument('--debug', const='', nargs='?', metavar='dest',
                       help='Debug (logs to DEST or stderr if DEST is omitted.')
        p.add_argument('-d', '--directory', default=os.getcwd(),
                       help='Download directory (default: CWD)')
        p.add_argument('-n', '--no-cache', action='store_true',
                       help='Disable cache')
        p.add_argument('-V', '--version', action='version',
                       version='%(prog)s v{}'.format(nctoutv.__version__))

        self._args = p.parse_args()

        if not os.path.isdir(self._args.directory):
            fmt = 'Error: "{}" is not a valid directory'
            print(fmt.format(self._args.directory), file=sys.stderr)
            sys.exit(1)

    def _init(self):
        logger_name = '{}.{}'.format(__name__, self.__class__.__name__)
        self._logger = logging.getLogger(logger_name)
        self._build_main_frame()
        self._build_popup_launcher()
        self._create_loop()
        self._create_client_thread()
        self._create_exit_pipe()
        self.set_status_msg('Loading TOU.TV shows...')
        #self._send_get_shows_request()

        self._logger.info('starting main loop')
        self._loop.run()

    def run(self):
        self._parse_args()

        if self._args.debug is not None:
            if len(self._args.debug) > 0:
                logging.basicConfig(level=logging.DEBUG, filename=self._args.debug)
            else:
                logging.basicConfig(level=logging.DEBUG)

        self._init()

        return 0

    def get_version(self):
        return nctoutv.__version__


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            app.request_exit()

        signal.signal(signal.SIGINT, handler)


def run():
    app = _App()
    _register_sigint(app)

    return app.run()
