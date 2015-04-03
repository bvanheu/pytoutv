import platform
import nctoutv
import signal
import urwid
import sys
import os


class App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow', 'dark blue', ('bold')),
        ('footer', '', 'dark green')
    ]

    def _build_main_frame_header(self):
        txt = [
            ('header-title', 'nctoutv v{}'.format(nctoutv.__version__)),
            '    Use the arrow keys to navigate, press ? for help'
        ]
        self._main_frame_header = urwid.AttrMap(urwid.Text(txt), 'header')

    def _build_main_frame_footer(self):
        txt = 'the footer'
        self._main_frame_footer = urwid.AttrMap(urwid.Text(txt), 'footer')

    def _build_main_frame(self):
        self._build_main_frame_header()
        self._build_main_frame_footer()
        body = urwid.Filler(urwid.Text('the body'), 'middle')
        self._main_frame = urwid.Frame(body=body,
                                       header=self._main_frame_header,
                                       footer=self._main_frame_footer)

    def _create_loop(self):
        self._loop = urwid.MainLoop(self._main_frame, App._palette)

    def __init__(self):
        self._build_main_frame()
        self._create_loop()

    @property
    def loop(self):
        return self._loop

    def run(self):
        self._loop.run()


def _register_sigint(app):
    if platform.system() == 'Linux':
        def handler(signal, frame):
            # TODO: find a better way to reset the terminal (using urwid)
            os.system('reset')
            sys.exit(1)

        signal.signal(signal.SIGINT, handler)


def run():
    app = App()
    _register_sigint(app)
    app.run()
