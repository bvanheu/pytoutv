import toutv.client
import platform
import nctoutv
import signal
import urwid
import sys
import os


class _BaseTreeWidget(urwid.TreeWidget):
    def __init__(self, node):
        super().__init__(node)
        self._w = urwid.AttrMap(self._w, 'node', 'selected-node')


class _BitrateTreeWidget(_BaseTreeWidget):
    def get_display_text(self):
        return self.get_node().get_value()

    def selectable(self):
        return True


class _EpisodeTreeWidget(_BaseTreeWidget):
    def get_display_text(self):
        return self.get_node().get_value().get_title()

    def selectable(self):
        return True


class _ShowTreeWidget(_BaseTreeWidget):
    def __init__(self, node):
        self._zok = 23
        super().__init__(node)
        self.expanded = False
        self.update_expanded_icon()

    def selectable(self):
        return True

    def load_inner_widget(self):
        return urwid.Text(self.get_node().get_value().get_title())

    def keypress(self, size, key):
        key = super().keypress(size, key)

        if key == ' ':
            title = self.get_node().get_value().get_title()

            if self.expanded:
                self._innerwidget.set_text(title)
            else:
                loading = '    [Loading...]'
                self._innerwidget.set_text([title, loading])

            # TODO: go back to idle, then draw screen, load children, and draw
            # screen again
            self.expanded = not self.expanded
            self.update_expanded_icon()

        return key


class _EpisodeNode(urwid.TreeNode):
    def __init__(self, emission, episode, app, key, parent=None):
        self._app = app
        self._emission = emission
        super().__init__(episode, key=key, parent=parent, depth=2)

    def load_widget(self):
        return _EpisodeTreeWidget(self)

    def set_status_emission_title(self):
        self._app.set_status_msg('Emission: {}'.format(self._emission.get_title()))


class _ShowNode(urwid.ParentNode):
    def __init__(self, emission, app, key, parent=None):
        self._app = app
        self._episodes = None
        super().__init__(emission, key=key, parent=parent, depth=1)

    def load_widget(self):
        return _ShowTreeWidget(self)

    def load_child_keys(self):
        if self._episodes is None:
            fmt = 'Loading episodes of {}...'
            self._app.set_status_msg(fmt.format(self.get_value().get_title()))
            self._episodes = self._app.client.get_emission_episodes(self.get_value())
            self._app.set_status_msg_okay()

        return sorted(list(self._episodes.keys()),
                      key=lambda e: self._episodes[e].get_title())

    def load_child_node(self, key):
        episode = self._episodes[key]

        return _EpisodeNode(self.get_value(), episode, self._app,
                            key=key, parent=self)


class _TopTreeWidget(urwid.TreeWidget):
    def get_display_text(self):
        return 'TOU.TV shows'

    def selectable(self):
        return True


class _TopNode(urwid.ParentNode):
    def __init__(self, app, parent=None):
        self._app = app
        self._emissions = None
        super().__init__(None, parent=parent, depth=0)

    def load_widget(self):
        return _TopTreeWidget(self)

    def load_child_keys(self):
        if self._emissions is None:
            self._app.set_status_msg('Loading shows...')
            self._emissions = self._app.client.get_emissions()
            self._app.set_status_msg_okay()

        return sorted(list(self._emissions.keys()),
                      key=lambda e: self._emissions[e].get_title())

    def load_child_node(self, key):
        emission = self._emissions[key]

        return _ShowNode(emission, self._app, key=key, parent=self)


class _ShowTreeListBox(urwid.TreeListBox):
    def __init__(self, app):
        self._app = app
        super().__init__(urwid.TreeWalker(_TopNode(app)))


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
            '    Use the arrow keys to navigate, press ? for help'
        ]
        self._oheader = urwid.Text(txt)
        self._oheader_wrap = urwid.AttrMap(self._oheader, 'header')

    def _build_loading_body(self):
        txt = urwid.Text('Loading TOU.TV shows...', align='center')
        self._obody = urwid.Filler(txt, 'middle')

    def _build_body(self):
        self._obody = _ShowTreeListBox(self._app)

    def _build_footer(self):
        txt = 'the footer'
        self._ofooter = urwid.Text(txt)
        self._ofooter_wrap = urwid.AttrMap(self._ofooter, 'footer')

    def set_show_tree(self):
        self._build_body()
        self.contents['body'] = (self._obody, None)

    def set_status_msg(self, msg):
        self._ofooter.set_text(msg)

    def set_status_msg_okay(self):
        self._ofooter.set_text('Okay')


class _MainLoop(urwid.MainLoop):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self._app = app
        self._inited = False

    def entering_idle(self):
        if not self._inited:
            self._inited = True
            self.draw_screen()
            self._app.set_show_tree()

        super().entering_idle()


class _App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow', 'dark blue', ('bold')),
        ('footer', '', 'dark green'),
        ('node', '', ''),
        ('selected-node', '', 'dark red'),
        ('node-loading', 'light red', ''),
        ('selected-node-loading', '', 'dark red'),
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

    def set_show_tree(self):
        self._main_frame.set_show_tree()

    def set_status_msg(self, msg):
        self._main_frame.set_status_msg(msg)

    def set_status_msg_okay(self):
        self._main_frame.set_status_msg_okay()

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
