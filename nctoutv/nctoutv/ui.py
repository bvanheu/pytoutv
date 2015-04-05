import re
import urwid


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

    def set_loading(self, show):
        del self._walker[:]
        fmt = 'Loading episodes of {}...'
        self._walker.append(urwid.Text(fmt.format(show.get_title())))

    def set_episodes(self, episodes):
        self._episodes = episodes

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
        if key == 'left' or key == 'esc':
            self._app.focus_shows()

            return None
        else:
            return super().keypress(size, key)


class _ShowWidget(urwid.Text):
    def __init__(self, show, **kwargs):
        self._emission = show
        super().__init__(show.get_title(), **kwargs)

    def selectable(self):
        return True

    @property
    def show(self):
        return self._emission

    def keypress(self, size, key):
        return key


class _ShowsLineBox(urwid.LineBox):
    def __init__(self, app, shows):
        self._app = app
        self._shows = shows
        self._build_listbox()
        super().__init__(self._listbox, title='TOU.TV shows')

    def _build_listbox(self):
        sorted_shows = sorted(self._shows.values(),
                              key=lambda e: e.get_title())
        self._shows_widgets = []
        shows_widgets_wrapped = []

        for show in sorted_shows:
            show_widget = _ShowWidget(show)
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
                self._app.show_episodes(show_widget.show)

                return None
        elif re.match('[0-9a-zA-Z]$', key):
            key_lc = key.lower()

            # q quits
            if key_lc == 'q':
                return super().keypress(size, key)

            for index, show_widget in enumerate(self._shows_widgets):
                show = show_widget.show
                title = show.get_title().lower()

                if key_lc == title[0]:
                    # TODO: cycle instead of focussing on the first
                    self._listbox.focus_position = index
                    break

            return None
        else:
            return super().keypress(size, key)

    def mark_current(self):
        focus = self._listbox.focus

        if focus is not None:
            self._marked = focus
            focus.set_attr_map({None: 'current-show'})

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

    def _get_version(self):
        version = self._app.get_version()
        v = version.split('.')

        return '.'.join(v[0:2])

    def _build_header(self):
        txt = [
            ('header-title', 'nctoutv v{}'.format(self._get_version())),
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

    def _build_footer(self):
        txt = 'the footer'
        self._ofooter = urwid.Text(txt)
        self._ofooter_wrap = urwid.AttrMap(self._ofooter, 'footer')

    def set_shows(self, shows):
        self._oshows_box = _ShowsLineBox(self._app, shows)
        self._oepisodes_box = _EpisodesLineBox(self._app)
        self._obody = urwid.Columns([self._oshows_box, self._oepisodes_box])
        self.contents['body'] = (self._obody, None)

    def set_status_msg(self, msg):
        self._ofooter.set_text(msg)

    def set_status_msg_okay(self):
        self._ofooter.set_text('Okay')

    def set_episodes(self, episodes):
        self._oepisodes_box.set_episodes(episodes)

    def set_episodes_loading(self, show):
        self._oepisodes_box.set_loading(show)

    def focus_episodes(self):
        if self._oepisodes_box.show_has_episodes():
            # mark current show widget
            self._oshows_box.mark_current()
            self._obody.focus_position = 1

    def focus_shows(self):
        self._oshows_box.unmark_current()
        self._obody.focus_position = 0
