from nctoutv.ui import _MainFrame
import toutv.client
import toutv.cache
import threading
import platform
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


def _get_client():
    try:
        cache = _get_cache()
    except:
        cache = toutv.cache.EmptyCache()

    return toutv.client.Client(cache=cache)


def _request_thread(app, rq):
    def process_get_shows(request):
        shows = client.get_emissions()
        app.set_shows(shows)

    def process_get_episodes(request):
        show = request.show
        episodes = client.get_emission_episodes(show)
        app.set_episodes(episodes, show)

    client = _get_client()
    rq_cb = {
        _GetShowsRequest: process_get_shows,
        _GetEpisodesRequest: process_get_episodes,
    }

    while True:
        request = rq.get()
        rq_cb[type(request)](request)


class _App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow,bold', 'dark blue'),
        ('header-key', 'white,bold', 'dark blue'),
        ('footer', 'black', 'dark green'),
        ('selected-item', 'default,standout', ''),
        ('current-show', 'white,bold', 'dark cyan'),
        ('show-title', 'default,bold', ''),
        ('key', 'default,bold', ''),
        ('sae', 'default,bold', ''),
        ('sae-selected', 'default,bold,standout', ''),
    ]

    def __init__(self):
        self._build_main_frame()
        self._create_loop()
        self._create_client_thread()

    def _build_main_frame(self):
        self._main_frame = _MainFrame(self)

    def _create_loop(self):
        self._loop = urwid.MainLoop(widget=self._main_frame,
                                    palette=_App._palette,
                                    unhandled_input=self._unhandled_input,
                                    handle_mouse=False)

    def _rt_wp_cb(self, unused=None):
        if self._last_cmd == 'set-shows':
            self._main_frame.set_shows(self._last_shows)
            self.set_status_msg_okay()
        elif self._last_cmd == 'set-episodes':
            self._main_frame.set_episodes(self._last_episodes, self._last_show)
            self._main_frame.focus_episodes()
            self.set_status_msg_okay()

    def _create_client_thread(self):
        self._rt_wp = self._loop.watch_pipe(self._rt_wp_cb)
        self._rt_queue = queue.Queue()
        self._rt = threading.Thread(target=_request_thread,
                                    args=[self, self._rt_queue], daemon=True)
        self._rt.start()

    def _unhandled_input(self, key):
        if key in ('q', 'Q', 'esc'):
            raise urwid.ExitMainLoop()
        elif key == '?':
            self.set_status_msg('pop help')

    def set_status_msg(self, msg):
        self._main_frame.set_status_msg(msg)

    def set_status_msg_okay(self):
        self._main_frame.set_status_msg_okay()

    def show_episodes(self, show):
        self._main_frame.set_episodes_info_loading(show)
        self._send_get_episodes_request(show)

    def focus_shows(self):
        self._main_frame.focus_shows()
        self._main_frame.set_episodes_info_select()

    def set_shows(self, shows):
        self._last_shows = shows
        self._last_cmd = 'set-shows'
        os.write(self._rt_wp, 'lol'.encode())

    def set_episodes(self, episodes, show):
        self._last_episodes = episodes
        self._last_show = show
        self._last_cmd = 'set-episodes'
        os.write(self._rt_wp, 'lol'.encode())

    def _send_request(self, request):
        if self._rt_queue.qsize() == 0:
            self._rt_queue.put(request)

            return True

        return False

    def _send_get_shows_request(self):
        self._send_request(_GetShowsRequest())

    def _send_get_episodes_request(self, show):
        if self._send_request(_GetEpisodesRequest(show)):
            fmt = 'Loading episodes of {}...'
            self.set_status_msg(fmt.format(show.get_title()))

    def run(self):
        self.set_status_msg('Loading TOU.TV shows...')
        self._send_get_shows_request()
        self._loop.run()

    def get_version(self):
        return nctoutv.__version__


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            # TODO: find a better way to reset the terminal (using urwid)
            os.system('reset')
            sys.exit(1)

        signal.signal(signal.SIGINT, handler)


def run():
    app = _App()
    _register_sigint(app)
    app.run()
