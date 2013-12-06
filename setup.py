# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from canossa import __version__, __license__, __author__

import inspect, os

filename = inspect.getfile(inspect.currentframe())
dirpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))

import canossa.line
canossa.line.test()
try:
    import canossa.tff
    import canossa.termprop
except:
    print "Please do:\n git submodule update --init"
    import sys
    sys.exit(1)

import canossa.cell as cell
import canossa.attribute as attribute
import canossa.line as line
import canossa.cursor as cursor
import canossa.screen as screen
import canossa.popup as popup
import canossa.output as output

import doctest
dirty = False
#for m in (attribute, cell, line, cursor, screen, popup, output):
for m in [attribute, cell]:
    failure_count, test_count = doctest.testmod(m)
    if failure_count > 0:
        dirty = True
if dirty:
    raise Exception("test failed.")


setup(name                  = 'canossa',
      version               = __version__,
      description           = 'Provides basic, transparent, off-screen(invisible) terminal emulation service, for terminal apps.',
      long_description      = open(dirpath + "/README.rst").read(),
      py_modules            = ['canossa'],
      eager_resources       = [],
      classifiers           = ['Development Status :: 4 - Beta',
                               'Topic :: Terminals',
                               'Environment :: Console',
                               'Intended Audience :: Developers',
                               'License :: OSI Approved :: GNU General Public License (GPL)',
                               'Programming Language :: Python'
                               ],
      keywords              = 'terminal',
      author                = __author__,
      author_email          = 'user@zuse.jp',
      url                   = 'https://github.com/saitoha/canossa',
      license               = __license__,
      packages              = find_packages(exclude=[]),
      zip_safe              = True,
      include_package_data  = False,
#      install_requires      = ['tff >=0.0.14, <0.1.0', 'termprop==0.0.1'],
      install_requires      = [],
      entry_points          = """
                              [console_scripts]
                              canossa = canossa:main
                              """
      )

