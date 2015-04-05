import collections
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


class _EnhancedListBox(urwid.ListBox):
    def keypress(self, size, key):
        if key == 'home':
            self.focus_position = 0
            self._invalidate()
        elif key == 'end':
            self.focus_position = len(self.body) - 1
            self._invalidate()

        return super().keypress(size, key)


class _EpisodesContents(urwid.WidgetWrap):
    def __init__(self):
        self._episodes_widgets = []
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
        self._listbox = _EnhancedListBox(self._walker)

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
        self._marked = None
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
        self._listbox = _EnhancedListBox(walker)

    def keypress(self, size, key):
        if key in ['right', 'enter']:
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

            # if the focussed widget already starts with this letter, cycle
            cur_show = self._listbox.focus.original_widget.show
            cur_show_title = cur_show.get_title()

            if cur_show_title[0].lower() == key_lc:
                # find show index
                for index, show_widget in enumerate(self._shows_widgets):
                    if show_widget.show is cur_show:
                        cur_show_index = index
                        break

                if cur_show_index != (len(self._shows_widgets) - 1):
                    next_show_index = cur_show_index + 1
                    next_show = self._shows_widgets[next_show_index].show
                    next_show_title = next_show.get_title()

                    if next_show_title[0].lower() == key_lc:
                        self._listbox.focus_position = next_show_index
                        return None

            for index, show_widget in enumerate(self._shows_widgets):
                show = show_widget.show
                title = show.get_title().lower()

                if key_lc == title[0]:
                    # TODO: cycle instead of focussing on the first
                    self._listbox.focus_position = index
                    break

            return None
        elif key == 'f1':
            cur_show = self._listbox.focus.original_widget.show
            self._app.show_show_info(cur_show)
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

    def set_current_show(self, show):
        for index, show_widget in enumerate(self._shows_widgets):
            show_candidate = show_widget.show
            if show_candidate is show:
                self._listbox.focus_position = index
                break

    def finish_search(self):
        self._listbox.focus.set_attr_map({None: None})

    def do_search(self, query, next=False):
        # reset the previous search result
        self._listbox.focus.set_attr_map({None: None})
        query = query.lower().strip()

        if len(query) == 0:
            return True

        # start the search at the current element (next one if next is True)
        next = 1 if next else 0
        items = collections.deque(enumerate(self._shows_widgets))
        items.rotate(-(self._listbox.focus_position + next))

        for index, show_widget in items:
            show = show_widget.show
            show_title = show.get_title().lower()

            if query in show_title:
                self._listbox.focus_position = index
                self._listbox.focus.set_attr_map({None: 'search-result'})
                return True

        self._listbox.focus.set_attr_map({None: None})

        return False


class _MainFrame(urwid.Frame):
    def __init__(self, app):
        self._app = app
        self._build_header()
        self._build_loading_body()
        self._build_info_box()
        self._build_footer()
        self._in_search = False
        super().__init__(body=self._oloading_body, header=self._oheader_wrap,
                         footer=self._ofooter_wrap)

    def _get_version(self):
        version = self._app.get_version()
        v = version.split('.')

        return '.'.join(v[0:2])

    def get_title_and_version(self):
        return 'nctoutv v{}'.format(self._get_version())

    def _build_header(self):
        txt = [
            ('header-title', self.get_title_and_version()),
            '    ',
            ('header-key', 'arrows'), ': nav    ',
            ('header-key', 'Enter'), ': view/action    ',
            ('header-key', 'Q'), ': quit    ',
            ('header-key', '?'), ': help',
        ]
        self._oheader_main = urwid.Text(txt)

        txt = [
            ('header-title', 'search'),
            '    ',
            ('header-key', 'F3'),
            ': next match    ',
            ('header-key', 'escape/enter'),
            ': finish search',
        ]
        self._oheader_search = urwid.Text(txt)
        self._oheader_wrap = urwid.AttrMap(self._oheader_main, 'header')

    def _set_header(self, header):
        self._oheader_wrap.original_widget = header

    def _build_loading_body(self):
        txt = urwid.Text('Loading TOU.TV shows...', align='center')
        self._oloading_body = urwid.Filler(txt, 'middle')

    def _build_footer(self):
        txt = 'the footer'
        self._ofooter_text = urwid.Text(txt)
        self._ofooter_search = urwid.Edit('/')
        self._ofooter_search_wrap = urwid.AttrMap(self._ofooter_search,
                                                  {None: None})
        self._ofooter_wrap = urwid.AttrMap(self._ofooter_text, 'footer')
        urwid.connect_signal(self._ofooter_search, 'change',
                             self._search_input_changed)

    def _build_info_box(self):
        self._oinfo_box_text = urwid.Text('info...')
        filler = urwid.Filler(self._oinfo_box_text, 'top')
        self._oinfo_box = urwid.LineBox(filler, title='Info')

    def set_shows(self, shows):
        self._oshows_box = _ShowsLineBox(self._app, shows)
        self._oepisodes_box = _EpisodesLineBox(self._app)
        self._olists = urwid.Columns([self._oshows_box, self._oepisodes_box])
        self._show_lists()

    def _show_info(self):
        self.contents['body'] = (self._oinfo_box, None)

    def _show_lists(self):
        self.contents['body'] = (self._olists, None)

    def show_show_info(self, show):
        self._oinfo_box.set_title(show.get_title())
        self._oinfo_box_text.set_text('title: {}'.format(show.get_title()))
        self._show_info()

    def set_status_msg(self, msg):
        self._ofooter_text.set_text(msg)

    def set_status_msg_okay(self):
        self._ofooter_text.set_text('Okay')

    def set_episodes(self, episodes, show):
        self._oepisodes_box.set_episodes(episodes, show)

    def set_episodes_info_loading(self, show):
        self._oepisodes_box.set_info_loading(show)

    def set_current_show(self, show):
        self._oshows_box.set_current_show(show)

    def _set_episodes_info_select(self):
        self._oepisodes_box.set_info_select()

    def focus_episodes(self):
        if self._oepisodes_box.has_episodes():
            # mark current show widget
            self._oshows_box.mark_current()
            self._olists.focus_position = 1

    def focus_shows(self):
        self._oshows_box.unmark_current()
        self._olists.focus_position = 0
        self._set_episodes_info_select()

    def _init_search(self):
        self._in_search = True
        self._ofooter_search.set_edit_text('')
        self._ofooter_wrap.original_widget = self._ofooter_search_wrap
        self.focus_position = 'footer'
        self._set_header(self._oheader_search)
        self._invalidate()

    def _finish_search(self):
        self._in_search = False
        self._oshows_box.finish_search()
        self.set_status_msg_okay()
        self._ofooter_wrap.original_widget = self._ofooter_text
        self.focus_position = 'body'
        self._set_header(self._oheader_main)
        self._invalidate()

    def _search_input_changed(self, _, new_text):
        assert(self._in_search)
        found = self._oshows_box.do_search(new_text)

        if found:
            attr_map = {None: None}
        else:
            # TODO: do not highlight the caption (/)
            attr_map = {None: 'footer-not-found'}

        self._ofooter_search_wrap.set_attr_map(attr_map)

    def keypress(self, size, key):
        if key == '/' and not self._in_search:
            if self.contents['body'] == (self._olists, None):
                self.focus_shows()
                self._init_search()

            return None
        elif key == 'f3' and self._in_search:
            self._oshows_box.do_search(self._ofooter_search.edit_text,
                                       next=True)

            return None
        elif key in ['enter', 'esc'] and self._in_search:
            self._finish_search()

            return None
        else:
            return super().keypress(size, key)


class _PopUpHelpText(urwid.Text):
    def __init__(self, popup_launcher):
        self._popup_launcher = popup_launcher
        super().__init__(self._get_markup())

    def _get_markup(self):
        return [
            ' ', ('header-key', 'F1'), ':     toggle selected show/episode info window\n',
            ' ', ('header-key', 'F9'), ':     toggle downloads window\n',
            '\n',
            ' ', ('header-key', '/'), ':      search show\n',
            ' ', ('header-key', 'F3'), ':     next search result\n',
            ' ', ('header-key', 'Escape'), ': exit search',
        ]

    def keypress(self, size, key):
        if key in ['q', 'Q', 'esc', '?']:
            self._popup_launcher.close_pop_up()

        return None


class _PopUpLauncher(urwid.PopUpLauncher):
    def __init__(self, frame):
        self._opened_popup = None
        super().__init__(frame)

    def create_pop_up(self):
        filler = urwid.Filler(_PopUpHelpText(self), 'top')

        return urwid.AttrMap(filler, 'header')

    def get_pop_up_parameters(self):
        params = {
            'left': len(self.original_widget.get_title_and_version()) + 3,
            'top': 1,
            'overlay_width': 57,
            'overlay_height': 6,
        }

        return params

    def close_pop_up(self):
        self._opened_popup = None
        super().close_pop_up()

    def keypress(self, size, key):
        if key == '?':
            if self._opened_popup is None:
                self._opened_popup = 'help'
                self.open_pop_up()
            else:
                self._opened_popup = None
                self.close_pop_up()

            return None
        elif key in ['q', 'Q', 'esc'] and self._opened_popup is not None:
            self._opened_popup = None
            self.close_pop_up()

            return None
        else:
            return super().keypress(size, key)
