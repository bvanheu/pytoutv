#!/usr/bin/env python
#
# Copyright (c) 2015, Philippe Proulx <eepp.ca>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the pytoutv nor the
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

import sys
from setuptools import setup


# Make sure we run Python 3.2+ here
v = sys.version_info

if v.major < 3 or v.minor < 2:
    sys.stderr.write('Sorry, toutvcli needs Python 3.2+\n')
    sys.exit(1)

# TODO: detect existing pytoutv<=2.3 project, and warn + quit if found


import nctoutv


setup(name='nctoutv',
      version=nctoutv.__version__,
      description='TOU.TV client TUI interface',
      author='Philippe Proulx',
      author_email='eeppeliteloop@gmail.com',
      url='https://github.com/bvanheu/pytoutv',
      keywords='TOUTV',
      license="BSD",
      packages=[
          'nctoutv'
      ],
      install_requires=[
          'toutvcore>=2.4.0',
          'urwid>=1.3.0',
      ],
      entry_points={
          'console_scripts': [
              'nctoutv = nctoutv.app:run'
          ],
      },
      # This allows to use "./setup.py test", although using
      # "./setup nosetests" provides more features.
      test_suite='nose.collector',
)
