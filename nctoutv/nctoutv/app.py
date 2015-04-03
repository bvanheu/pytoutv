import platform
import nctoutv
import signal
import urwid
import sys
import os


class MainFrame(urwid.Frame):
    def __init__(self):
        self._build_header()
        self._build_body()
        self._build_footer()
        super().__init__(body=self._obody, header=self._oheader_wrap,
                         footer=self._ofooter_wrap)

    def _build_header(self):
        txt = [
            ('header-title', 'nctoutv v{}'.format(nctoutv.__version__)),
            '    Use the arrow keys to navigate, press ? for help'
        ]
        self._oheader = urwid.Text(txt)
        self._oheader_wrap = urwid.AttrMap(self._oheader, 'header')

    def _build_body(self):
        self._obody = urwid.Filler(urwid.Text('the body'), 'middle')

    def _build_footer(self):
        txt = 'the footer'
        self._ofooter = urwid.Text(txt)
        self._ofooter_wrap = urwid.AttrMap(self._ofooter, 'footer')

    def test(self):
        self._oheader.set_text('caca')

class App:
    _palette = [
        ('header', 'white', 'dark blue'),
        ('header-title', 'yellow', 'dark blue', ('bold')),
        ('footer', '', 'dark green')
    ]

    def __init__(self):
        self._build_main_frame()
        self._create_loop()

    def _build_main_frame(self):
        self._main_frame = MainFrame()

    def _create_loop(self):
        self._loop = urwid.MainLoop(self._main_frame, App._palette,
                                    unhandled_input=self._unhandled_input)

    def _unhandled_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == '?':
            self._main_frame.test()

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
