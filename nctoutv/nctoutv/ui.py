import collections
import re
import urwid

"""
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
"""

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
    _DEFAULT_TITLE = 'Episodes'

    def __init__(self, app):
        self._app = app
        self._contents = _EpisodesContents()
        super().__init__(self._contents, title=_EpisodesLineBox._DEFAULT_TITLE)

    def keypress(self, size, key):
        if key in ['left', 'esc', 'backspace']:
            self._app.focus_shows()
            self.set_title('Episodes')

            return None
        else:
            return super().keypress(size, key)

    def _set_default_title(self):
        self.set_title(_EpisodesLineBox._DEFAULT_TITLE)

    def set_info_loading(self, show):
        self._set_default_title()
        self._contents.set_info_loading(show)

    def set_info_select(self):
        self._set_default_title()
        self._contents.set_info_select()

    def set_episodes(self, episodes, show):
        self._contents.set_episodes(episodes, show)

        if episodes:
            plural = '' if len(episodes) == 1 else 's'
            self.set_title('{} episode{}'.format(len(episodes), plural))
        else:
            self._set_default_title()

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

"""
class _ShowsListBox(_EnhancedListBox):
    def __init__(self, app, shows):
        self._app = app
        self._shows = shows
        self._marked = None
        self._build_walker()
        super().__init__(self._walker)

    def _build_walker(self):
        sorted_shows = sorted(self._shows.values(),
                              key=lambda e: e.get_title())
        self._shows_widgets = []
        shows_widgets_wrapped = []

        for show in sorted_shows:
            show_widget = _ShowWidget(show)
            self._shows_widgets.append(show_widget)
            wrapper = urwid.AttrMap(show_widget, None, 'selected-item')
            shows_widgets_wrapped.append(wrapper)

        self._walker = urwid.SimpleListWalker(shows_widgets_wrapped)

    def _get_focussed_show(self):
        return self.focus.original_widget.show

    def keypress(self, size, key):
        if key in ['right', 'enter']:
            if self.focus is not None:
                show_widget = self.focus.original_widget
                self._app.show_episodes(show_widget.show)

                return None
        elif re.match('[0-9a-zA-Z]$', key):
            key_lc = key.lower()

            # q quits
            if key_lc == 'q':
                return super().keypress(size, key)

            # if the focussed widget already starts with this letter, cycle
            cur_show = self._get_focussed_show()
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
                        self.focus_position = next_show_index
                        return None

            for index, show_widget in enumerate(self._shows_widgets):
                show = show_widget.show
                title = show.get_title().lower()

                if key_lc == title[0]:
                    # TODO: cycle instead of focussing on the first
                    self.focus_position = index
                    break

            return None
        elif key == 'f1':
            self._app.show_show_info(self._get_focussed_show())
        else:
            return super().keypress(size, key)

    def mark_current(self):
        if self.focus is not None:
            self._marked = self.focus
            self.focus.set_attr_map({None: 'current-show'})

    def unmark_current(self):
        if self._marked is not None:
            self._marked.set_attr_map({None: None})

    def set_current_show(self, show):
        for index, show_widget in enumerate(self._shows_widgets):
            show_candidate = show_widget.show
            if show_candidate is show:
                self.focus_position = index
                break

    def finish_search(self):
        self.focus.set_attr_map({None: None})

    def do_search(self, query, next=False):
        # reset the previous search result
        self.focus.set_attr_map({None: None})
        query = query.lower().strip()

        if len(query) == 0:
            return True

        # start the search at the current element (next one if next is True)
        next = 1 if next else 0
        items = collections.deque(enumerate(self._shows_widgets))
        items.rotate(-(self.focus_position + next))

        for index, show_widget in items:
            show = show_widget.show
            show_title = show.get_title().lower()

            if query in show_title:
                self.focus_position = index
                self.focus.set_attr_map({None: 'search-result'})
                return True

        self.focus.set_attr_map({None: None})

        return False


class _ShowInfo(urwid.LineBox):
    def __init__(self, frame):
        self._frame = frame
        self._text = urwid.Text('')
        filler = urwid.Filler(self._text, 'top')
        wrap = urwid.WidgetWrap(filler)
        super().__init__(wrap, title='Info')

    def keypress(self, size, key):
        if key in ['q', 'Q', 'esc']:
            self._frame.close_show_info()

            return None

        return super().keypress(size, key)

    def selectable(self):
        return True

    def set_show(self, show):
        self.set_title(show.get_title())
        network = show.get_network()

        if network is None:
            network = 'unknown'

        country = show.get_country()

        if country is None:
            country = 'unknown'

        year = show.get_year()
        year_markup = []

        if year is not None:
            year_markup = ['(', year, ')']

        markup = [
            ('show-info-title', show.get_title())
        ]
        markup += year_markup
        markup += [
            '\n',
            '\n',
            ('show-info', 'Network'), ': ', network, '\n',
            ('show-info', 'Country'), ': ', country, '\n',
            '\n',
            show.get_description(),
        ]
        self._text.set_text(markup)

"""
class _SearchEdit(urwid.Edit):
    def __init__(self, frame):
        self._frame = frame
        super().__init__('/')

    def keypress(self, size, key):
        if key == 'f3':
            self._frame.do_search_next(self.edit_text)
        elif key in ['enter', 'esc']:
            self._frame.finish_search()
        else:
            # unhandled keys; we do not return to stop propagation here
            super().keypress(size, key)

        return None


class _BasicList(urwid.LineBox):
    '''Base for Shows and Episodes lists'''

    def __init__(self, title, inactive_text):
        self._walker = urwid.SimpleListWalker([])
        self._list = urwid.ListBox(self._walker)

        self._inactive_text = urwid.Filler(urwid.Text(inactive_text,
                                                      align='center'))
        self._wrap = urwid.WidgetWrap(self._inactive_text)
        super(_BasicList, self).__init__(self._wrap, title=title)

    def set_content(self, content):
        self._walker.clear()
        self._walker.extend(content)

    def show_list(self):
        self._wrap.original_widget = self._list

    def show_inactive_text(self):
        self._wrap.original_widget = self._inactive_text


class _ShowsList(_BasicList):

    def __init__(self):
        super(_ShowsList, self).__init__('Shows', 'Loading shows...')


class _EpisodesList(_BasicList):

    def __init__(self):
        super(_EpisodesList, self).__init__('Episodes', 'Please select a show.')

class _EpisodesBrowser(urwid.Columns):
    def __init__(self, app):
        self._shows_list = _ShowsList()
        self._episodes_list = _EpisodesList()
        super(_EpisodesBrowser, self).__init__([self._shows_list,
                                                self._episodes_list])

class _BottomPane(urwid.LineBox):
    def __init__(self, app):
        self._build_pages()
        self._wrap = urwid.WidgetPlaceholder(None)
        super(_BottomPane, self).__init__(self._wrap)
        self.show_page(self._get_first_page_name())
        self._app = app

    def _get_first_page_name(self):
        return list(self._pages.keys())[0]

    def _build_pages(self):
        self._pages = collections.OrderedDict()
        self._build_page_info()
        self._build_page_downloads()

    def _build_page_info(self):
        txt = urwid.Filler(urwid.Text('INFO :D'), valign='top')
        self._pages['info'] = (txt, 'Information')

    def _build_page_downloads(self):
        txt = urwid.Filler(urwid.Text('DOWNLOADS :D'), valign='top')
        self._pages['downloads'] = (txt, 'Downloads')

    def show_page(self, page_name):
        if page_name in self._pages:
            page = self._pages[page_name]
            self.set_title(page[1])
            self._wrap.original_widget = page[0]
        else:
            # TODO: log
            pass


class _AppBody(urwid.Pile):
    def __init__(self, app):
        self._app = app
        self._episodes_browser = _EpisodesBrowser(app)
        self._bottom_pane = _BottomPane(app)
        super(_AppBody, self).__init__([('weight', 3, self._episodes_browser),
                                        ('weight', 1, self._bottom_pane)])

    @property
    def bottom_pane(self):
        return self._bottom_pane

class _MainFrame(urwid.Frame):
    def __init__(self, app):
        self._app = app
        self._build_header()
        self._build_body()
        self._build_footer()
        self._in_search = False
        super().__init__(header=self._oheader_wrap,
                         body=self._obody,
                         footer=self._ofooter_wrap)

    def _get_version(self):
        return self._app.get_version()

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
        self._ofooter_search = _SearchEdit(self)
        self._ofooter_search_wrap = urwid.AttrMap(self._ofooter_search,
                                                  {None: None})
        self._ofooter_wrap = urwid.AttrMap(self._ofooter_text, 'footer')
        urwid.connect_signal(self._ofooter_search, 'change',
                             self._search_input_changed)

    def _build_body(self):
        self._obody = _AppBody(self._app)

    def set_shows(self, shows):
        self._oshows_list = _ShowsListBox(self._app, shows)
        self._oshows_box = urwid.LineBox(self._oshows_list,
                                         title='TOU.TV shows')
        self._oepisodes_box = _EpisodesLineBox(self._app)
        self._olists = urwid.Columns([self._oshows_box, self._oepisodes_box])
        self._show_lists()

    def set_status_msg(self, msg):
        self._ofooter_text.set_text(msg)

    def set_status_msg_okay(self):
        self._ofooter_text.set_text('Okay')

    def set_episodes(self, episodes, show):
        self._oepisodes_box.set_episodes(episodes, show)

    def set_episodes_info_loading(self, show):
        self._oepisodes_box.set_info_loading(show)

    def set_current_show(self, show):
        self._oshows_list.set_current_show(show)

    def _set_episodes_info_select(self):
        self._oepisodes_box.set_info_select()

    def focus_episodes(self):
        if self._oepisodes_box.has_episodes():
            # mark current show widget
            self._oshows_list.mark_current()
            self._olists.focus_position = 1

    def focus_shows(self):
        self._oshows_list.unmark_current()
        self._olists.focus_position = 0
        self._set_episodes_info_select()

    def _init_search(self):
        self._in_search = True
        self._ofooter_search.set_edit_text('')
        self._ofooter_wrap.original_widget = self._ofooter_search_wrap
        self.focus_position = 'footer'
        self._set_header(self._oheader_search)
        self._invalidate()

    def finish_search(self):
        self._in_search = False
        self._oshows_list.finish_search()
        self.set_status_msg_okay()
        self._ofooter_wrap.original_widget = self._ofooter_text
        self.focus_position = 'body'
        self._set_header(self._oheader_main)
        self._invalidate()

    def do_search_next(self, query):
        self._oshows_list.do_search(query, next=True)

    def _search_input_changed(self, _, new_text):
        assert(self._in_search)
        found = self._oshows_list.do_search(new_text)

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
        elif key == 'f5':
            self._obody.bottom_pane.show_page('info')
        elif key == 'f6':
            self._obody.bottom_pane.show_page('downloads')
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
        key = super().keypress(size, key)

        if key == '?':
            if self._opened_popup is None:
                self._opened_popup = 'help'
                self.open_pop_up()
            else:
                self._opened_popup = None
                self.close_pop_up()
        elif key in ['q', 'Q', 'esc'] and self._opened_popup is not None:
            self._opened_popup = None
            self.close_pop_up()

        return key
