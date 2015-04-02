# Copyright (c) 2014, Philippe Proulx <eepp.ca>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of pytoutv nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Philippe Proulx BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import shutil

try:
    from termcolor import colored
    _has_termcolor = True
except ImportError:
    _has_termcolor = False


class ProgressBar:
    def __init__(self, filename, segments_count):
        self._filename = filename
        self._segments_count = segments_count

    @staticmethod
    def _get_terminal_width():
        if hasattr(shutil, 'get_terminal_size'):
            return shutil.get_terminal_size()[0]
        else:
            return 80

    def _get_bar_widget(self, width):
        total_segments = self._total_segments
        inner_width = width - 2
        plain = round(total_segments / self._segments_count * inner_width)
        empty = inner_width - plain
        empty_s = '-' * empty

        if _has_termcolor:
            empty_s = colored(empty_s, attrs=['dark'])

        bar = '[{}{}]'.format('#' * plain, empty_s)

        return bar

    def _get_percent_widget(self, width):
        total_segments = self._total_segments
        percent = int(total_segments / self._segments_count * 100)
        base = '{}%'.format(percent)

        return base.rjust(width)

    def _get_segments_widget(self, width):
        total_segments = self._total_segments
        base = '{}/{}'.format(total_segments, self._segments_count)

        return base.rjust(width)

    def _get_size_widget(self, width):
        total_bytes = self._total_bytes

        if total_bytes < (1 << 10):
            base = '{} B'.format(total_bytes)
        elif total_bytes < (1 << 20):
            base = '{:.1f} kiB'.format(total_bytes / (1 << 10))
        elif total_bytes < (1 << 30):
            base = '{:.1f} MiB'.format(total_bytes / (1 << 20))
        else:
            base = '{:.1f} GiB'.format(total_bytes / (1 << 30))

        return base.rjust(width)

    def _get_filename_widget(self, width):
        filename_len = len(self._filename)

        if filename_len < width:
            s = self._filename.ljust(width)
        else:
            s = '{}...'.format(self._filename[:width - 3])

        if _has_termcolor and self._total_segments != self._segments_count:
            s = colored(s, attrs=['bold'])

        return s

    def get_bar(self, total_segments, total_bytes):
        # Different required widths for widgets
        self._total_segments = total_segments
        self._total_bytes = total_bytes
        term_width = ProgressBar._get_terminal_width()
        percent_width = 5
        size_width = 12
        segments_width = len(str(self._segments_count)) * 2 + 4
        padding = 1
        fixed_width = percent_width + size_width + segments_width + padding
        variable_width = term_width - fixed_width
        filename_width = round(variable_width * 0.6)
        bar_width = variable_width - filename_width

        # Get all widgets
        wpercent = self._get_percent_widget(percent_width)
        wsize = self._get_size_widget(size_width)
        wsegments = self._get_segments_widget(segments_width)
        wfilename = self._get_filename_widget(filename_width)
        wbar = self._get_bar_widget(bar_width)

        # Build line
        line = '{}{}{} {}{}'.format(wfilename, wsize, wsegments, wbar,
                                    wpercent)

        return line
