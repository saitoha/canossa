#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ***** BEGIN LICENSE BLOCK *****
# Copyright (C) 2012-2014, Hayaki Saito
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
# ***** END LICENSE BLOCK *****

from stub import *

def _printver():
        import __init__
        print '''
canossa %s
Copyright (C) 2012 Hayaki Saito <user@zuse.jp>.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses/.
        ''' % __init__.__version__
        return

def create(row, col, y, x, termenc, termprop, visibility=False):
    import output, screen

    screen = screen.Screen(row, col, y, x, termenc, termprop)
    return output.Canossa(screen, visibility=visibility)

def main():
    import sys, os, optparse, select
    # parse options and arguments
    usage = 'usage: %prog [options] command'
    parser = optparse.OptionParser(usage=usage)

    parser.add_option('-v', '--visible', dest='visibility',
                      action="store_true", default=False,
                      help='bring up the front of terminal (visible mode)')

    parser.add_option('--version', dest='version',
                      action="store_true", default=False,
                      help='show version')

    (options, args) = parser.parse_args()

    # print version
    if options.version:
        _printver()
        return

    # retrive starting command
    if len(args) > 0:
        command = args[0]
    elif not os.getenv('SHELL') is None:
        command = os.getenv('SHELL')
    else:
        command = '/bin/sh'

    # retrive TERM setting
    if not os.getenv('TERM') is None:
        term = os.getenv('TERM')
    else:
        term = 'xterm'

    # retrive LANG setting
    if not os.getenv('LANG') is None:
        lang = os.getenv('LANG')
    else:
        import locale
        lang = '%s.%s' % locale.getdefaultlocale()

    # retrive terminal encoding setting
    import locale
    language, encoding = locale.getdefaultlocale()
    termenc = encoding

    import output

    # create pty
    tty = tff.DefaultPTY(term, lang, command, sys.stdin)

    # fit to screen and get size
    tty.fitsize()

    # make screen
    if options.visibility:
        outputhandler = output.Canossa(visibility=True, termenc=termenc)
    else:
        canossahandler = output.Canossa(visibility=False, termenc=termenc)
        outputhandler = tff.FilterMultiplexer(canossahandler, tff.DefaultHandler())

    # create TFF session
    session = tff.Session(tty)

    # start session
    session.start(termenc=termenc,
                  stdin=sys.stdin,
                  stdout=sys.stdout,
                  outputhandler=outputhandler,
                  buffering=False)


''' main '''
if __name__ == '__main__':
    main()

