import toutv.client
import platform
import nctoutv
import signal
import urwid
import sys
import os


class _EpisodeWidget(urwid.Text):
    def __init__(self, episode, **kwargs):
        self._episode = episode
        super().__init__(episode.get_title(), **kwargs)

    def selectable(self):
        return True

    @property
    def episode(self):
        return self._episode

    def keypress(self, size, key):
        return key


class _EpisodesLineBox(urwid.LineBox):
    def __init__(self, app):
        self._app = app
        self._build_listbox()
        super().__init__(self._listbox, title="Selected show's episodes")

    def _build_listbox(self):
        txt = 'Please select a show and press Enter'
        self._walker = urwid.SimpleFocusListWalker([urwid.Text(txt)])
        self._listbox = urwid.ListBox(self._walker)

    def set_emission(self, emission):
        self._episodes = self._app.client.get_emission_episodes(emission)

        try:
            episodes = sorted(self._episodes.values(),
                              key=lambda e: e.DateSeasonEpisode)
        except:
            episodes = sorted(self._episodes.values(),
                              key=lambda e: e.get_title())

        self._episodes_widgets = []
        episodes_widgets_wrapped = []

        for episode in episodes:
            episode_widget = _EpisodeWidget(episode)
            self._episodes_widgets.append(episode_widget)
            wrapper = urwid.AttrMap(episode_widget, None, 'selected-item')
            episodes_widgets_wrapped.append(wrapper)

        del self._walker[:]

        if episodes_widgets_wrapped:
            self._walker += episodes_widgets_wrapped
        else:
            self._walker.append(urwid.Text('This show has no episodes'))

    def show_has_episodes(self):
        return len(self._episodes_widgets) > 0

    def keypress(self, size, key):
        if key == 'left' or key == 'escape':
            self._app.focus_shows()

            return None
        else:
            return super().keypress(size, key)


class _ShowWidget(urwid.Text):
    def __init__(self, emission, **kwargs):
        self._emission = emission
        super().__init__(emission.get_title(), **kwargs)

    def selectable(self):
        return True

    @property
    def emission(self):
        return self._emission

    def keypress(self, size, key):
        return key


class _ShowsLineBox(urwid.LineBox):
    def __init__(self, app):
        self._app = app
        self._build_listbox()
        super().__init__(self._listbox, title='TOU.TV shows')

    def _build_listbox(self):
        self._emissions = self._app.client.get_emissions()
        emissions = sorted(self._emissions.values(),
                           key=lambda e: e.get_title())
        self._shows_widgets = []
        shows_widgets_wrapped = []

        for emission in emissions:
            show_widget = _ShowWidget(emission)
            self._shows_widgets.append(show_widget)
            wrapper = urwid.AttrMap(show_widget, None, 'selected-item')
            shows_widgets_wrapped.append(wrapper)

        walker = urwid.SimpleListWalker(shows_widgets_wrapped)
        self._listbox = urwid.ListBox(walker)

    def keypress(self, size, key):
        if key == 'right' or key == 'enter':
            focus = self._listbox.focus

            if focus is not None:
                show_widget = focus.original_widget
                self._app.show_emission_episodes(show_widget.emission)
                self._app.focus_episodes()

                return None
        else:
            return super().keypress(size, key)

    def mark_current(self):
        focus = self._listbox.focus

        if focus is not None:
            self._marked = focus
            focus.set_attr_map({None: 'selected-item'})

    def unmark_current(self):
        if self._marked is not None:
            self._marked.set_attr_map({None: None})


class _MainFrame(urwid.Frame):
    def __init__(self, app):
        self._app = app
        self._build_header()
        self._build_loading_body()
        self._build_footer()
        super().__init__(body=self._obody, header=self._oheader_wrap,
                         footer=self._ofooter_wrap)

    @staticmethod
    def _get_version():
        v = nctoutv.__version__.split('.')

        return '.'.join(v[0:2])

    def _build_header(self):
        txt = [
            ('header-title', 'nctoutv v{}'.format(_MainFrame._get_version())),
            '    ',
            ('header-key', 'arrows'),
            ': navigate    ',
            ('header-key', 'Enter'),
            ': view/action    ',
            ('header-key', '?'),
            ': help',
        ]
        self._oheader = urwid.Text(txt)
        self._oheader_wrap = urwid.AttrMap(self._oheader, 'header')

    def _build_loading_body(self):
        txt = urwid.Text('Loading TOU.TV shows...', align='center')
        self._obody = urwid.Filler(txt, 'middle')

    def _build_body(self):
        self._oshows_box = _ShowsLineBox(self._app)
        self._oepisodes_box = _EpisodesLineBox(self._app)
        self._obody = urwid.Columns([self._oshows_box, self._oepisodes_box])

    def _build_footer(self):
        txt = 'the footer'
        self._ofooter = urwid.Text(txt)
        self._ofooter_wrap = urwid.AttrMap(self._ofooter, 'footer')

    def display_lists(self):
        self._build_body()
        self.contents['body'] = (self._obody, None)

    def set_status_msg(self, msg):
        self._ofooter.set_text(msg)

    def set_status_msg_okay(self):
        self._ofooter.set_text('Okay')

    def show_emission_episodes(self, emission):
        self._oepisodes_box.set_emission(emission)

    def focus_episodes(self):
        if self._oepisodes_box.show_has_episodes():
            # mark current show widget
            self._oshows_box.mark_current()
            self._obody.focus_position = 1

    def focus_shows(self):
        self._oshows_box.unmark_current()
        self._obody.focus_position = 0


class _MainLoop(urwid.MainLoop):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._inited = False

    def entering_idle(self):
        if not self._inited:
            self._inited = True
            self.draw_screen()
            self._app.display_lists()

        self._app.on_idle()
        super().entering_idle()


class _App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow,bold', 'dark blue'),
        ('header-key', 'white,bold', 'dark blue'),
        ('footer', '', 'dark green'),
        ('selected-item', 'white', 'dark red'),
    ]

    def __init__(self):
        self._build_client()
        self._build_main_frame()
        self._create_loop()

    @staticmethod
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

    def _build_client(self):
        self._client = toutv.client.Client(cache=_App._get_cache())

    def _build_main_frame(self):
        self._main_frame = _MainFrame(self)

    def _create_loop(self):
        self._loop = _MainLoop(self, widget=self._main_frame,
                               palette=_App._palette,
                               unhandled_input=self._unhandled_input)

    def _unhandled_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == '?':
            self.set_status_msg('pop help')

    @property
    def client(self):
        return self._client

    def on_idle(self):
        pass

    def display_lists(self):
        self._main_frame.display_lists()

    def set_status_msg(self, msg):
        self._main_frame.set_status_msg(msg)

    def set_status_msg_okay(self):
        self._main_frame.set_status_msg_okay()

    def show_emission_episodes(self, emission):
        self._main_frame.show_emission_episodes(emission)

    def focus_episodes(self):
        self._main_frame.focus_episodes()

    def focus_shows(self):
        self._main_frame.focus_shows()


    def run(self):
        self.set_status_msg_okay()
        self._loop.run()


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
