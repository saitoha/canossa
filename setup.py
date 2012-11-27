# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from canossa import __version__, __license__, __author__

import canossa.line
canossa.line.test()

setup(name                  = 'canossa',
      version               = __version__,
      description           = 'Provides basic, transparent, off-screen(invisible) terminal emulation service, for terminal apps.',
      long_description      = open("README.rst").read(),
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
      install_requires      = ['tff >=0.0.13, <0.1.0'],
      entry_points          = """
                              [console_scripts]
                              canossa = canossa:main
                              """
      )

