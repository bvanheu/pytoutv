import re
import urwid


class _EpisodeWidget(urwid.Text):
    def __init__(self, episode, **kwargs):
        self._episode = episode
        markup = []

        if episode.get_sae() is not None:
            markup += [
                '[',
                ('sae', episode.get_sae()),
                '] ',
            ]

        markup.append(episode.get_title())
        super().__init__(markup, **kwargs)

    def selectable(self):
        return True

    @property
    def episode(self):
        return self._episode

    def keypress(self, size, key):
        return key


class _EpisodesContents(urwid.WidgetWrap):
    def __init__(self):
        self._episodes_widgets = None
        self._build_listbox()
        super().__init__(urwid.Text(''))
        self.set_info_select()

    def _set_info(self, markup):
        text = urwid.Text(markup, align='center')
        filler = urwid.Filler(text, 'middle')
        self._set_w(filler)

    def set_info_loading(self, show):
        markup = [
            'Loading episodes of ',
            ('show-title', show.get_title()),
            '...'
        ]
        self._set_info(markup)

    def set_info_select(self):
        markup = [
            'Select a show and press ',
            ('key', 'Enter'),
        ]
        self._set_info(markup)

    def _build_listbox(self):
        self._walker = urwid.SimpleFocusListWalker([])
        self._listbox = urwid.ListBox(self._walker)

    def set_episodes(self, episodes, show):
        self._episodes = episodes

        try:
            episodes = sorted(self._episodes.values(),
                              key=lambda e: e.AirDateFormated)
        except:
            episodes = sorted(self._episodes.values(),
                              key=lambda e: e.get_title())

        self._episodes_widgets = []
        episodes_widgets_wrapped = []

        for episode in episodes:
            episode_widget = _EpisodeWidget(episode)
            self._episodes_widgets.append(episode_widget)
            normal_map = {
                'sae': 'sae',
            }
            focus_map= {
                'sae': 'sae-selected',
                None: 'selected-item',
            }
            wrapper = urwid.AttrMap(episode_widget, normal_map, focus_map)
            episodes_widgets_wrapped.append(wrapper)

        if episodes_widgets_wrapped:
            del self._walker[:]
            self._walker += episodes_widgets_wrapped
            self._set_w(self._listbox)
        else:
            markup = [
                ('show-title', show.get_title()),
                ' has no episodes'
            ]
            self._set_info(markup)

    def has_episodes(self):
        return len(self._episodes_widgets) > 0


class _EpisodesLineBox(urwid.LineBox):
    def __init__(self, app):
        self._app = app
        self._contents = _EpisodesContents()
        super().__init__(self._contents, title='Episodes')

    def keypress(self, size, key):
        if key in ['left', 'esc', 'backspace']:
            self._app.focus_shows()
            self.set_title('Episodes')

            return None
        else:
            return super().keypress(size, key)

    def set_info_loading(self, show):
        self._contents.set_info_loading(show)

    def set_info_select(self):
        self._contents.set_info_select()

    def set_episodes(self, episodes, show):
        self._contents.set_episodes(episodes, show)

        if episodes:
            plural = '' if len(episodes) == 1 else 's'
            self.set_title('{} episode{}'.format(len(episodes), plural))
        else:
            self.set_title('Episodes')

    def has_episodes(self):
        return self._contents.has_episodes()


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
            ': nav    ',
            ('header-key', 'Enter'),
            ': view/action    ',
            ('header-key', 'Q'),
            ': quit    ',
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

    def set_episodes(self, episodes, show):
        self._oepisodes_box.set_episodes(episodes, show)

    def set_episodes_info_loading(self, show):
        self._oepisodes_box.set_info_loading(show)

    def set_episodes_info_select(self):
        self._oepisodes_box.set_info_select()

    def focus_episodes(self):
        if self._oepisodes_box.has_episodes():
            # mark current show widget
            self._oshows_box.mark_current()
            self._obody.focus_position = 1

    def focus_shows(self):
        self._oshows_box.unmark_current()
        self._obody.focus_position = 0
