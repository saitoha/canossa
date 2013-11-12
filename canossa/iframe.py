#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ***** BEGIN LICENSE BLOCK *****
# Copyright (C) 2012  Hayaki Saito <user@zuse.jp>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ***** END LICENSE BLOCK *****


import tff
from mouse import IFocusListener, IMouseListener, MouseDecoder
from interface import IInnerFrame, IInnerFrameListener
from output import Canossa
from screen import Screen

_HITTEST_NONE              = 0
_HITTEST_CLIENTAREA        = 1
_HITTEST_TITLEBAR          = 2
_HITTEST_FRAME_LEFT        = 3
_HITTEST_FRAME_TOP         = 4
_HITTEST_FRAME_RIGHT       = 5
_HITTEST_FRAME_BOTTOM      = 6
_HITTEST_FRAME_TOPLEFT     = 7
_HITTEST_FRAME_TOPRIGHT    = 8
_HITTEST_FRAME_BOTTOMLEFT  = 9
_HITTEST_FRAME_BOTTOMRIGHT = 10


class IFocusListenerImpl(IFocusListener):

    """ IFocusListener implementation """
    def onfocusin(self):
        pass

    def onfocusout(self):
        self.close()


class IMouseListenerImpl(IMouseListener):

    _lasthittest = None
    _dragpos = None

    """ IMouseListener implementation """

    def mouseenabled(self):
        return True

    def onmousedown(self, context, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            context.puts(u"\x1b[M%c%c%c" % (0 + 32, x + 33, y + 33))

    def onmouseup(self, context, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            context.puts(u"\x1b[M%c%c%c" % (3 + 32, x + 33, y + 33))

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            self.onfocusout()

    def ondoubleclick(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            self.onfocusout()

    def onmousehover(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            context.puts(u"\x1b[M%c%c%c" % (32 + 32, x + 33, y + 33))

    """ scroll """
    def onscrolldown(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            context.puts(u"\x1b[M%c%c%c" % (64 + 32, x + 33, y + 33))

    def onscrollup(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            context.puts(u"\x1b[M%c%c%c" % (65 + 32, x + 33, y + 33))

    """ drag and drop """
    def ondragstart(self, s, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_TITLEBAR:
            self._dragpos = (x, y)
        elif hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            pass

    def ondragend(self, s, x, y):
        self.left += self.offset_left
        self.top += self.offset_top
        self.offset_left = 0
        self.offset_top = 0
        self._dragpos = None

    def moveTo(self, left, top):
        self.left = left
        self.top = top

    def ondragmove(self, context, x, y):
        if self._dragpos:
            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._outerscreen
            innerscreen = self.innerscreen

            width = innerscreen.width + 2
            height = innerscreen.height + 2

            if self.left + offset_x - 1 < 0:
                offset_x = 1 - self.left
            elif self.left + width + offset_x - 1 > screen.width:
                offset_x = screen.width - self.left - width + 1
            if self.top + offset_y - 1 < 0:
                offset_y = 1 - self.top
            elif self.top + height + offset_y - 1 > screen.height:
                offset_y = screen.height - self.top - height + 1

            self.offset_left = offset_x
            self.offset_top = offset_y

            left = self.left + self.offset_left - 1
            top = self.top + self.offset_top - 1
            width = innerscreen.width + 2
            height = innerscreen.height + 2
            self._window.realloc(left, top, width, height)
        else:
            hittest = self._hittest(x, y)
            if hittest == _HITTEST_CLIENTAREA:
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                context.puts("\x1b[M%c%c%c" % (32 + 32, x + 33, y + 33))

    def _get_left(self):
        return self.left + self.offset_left - 1

    def _get_right(self):
        return self.left + self.offset_left + self.innerscreen.width + 1

    def _get_top(self):
        return self.top + self.offset_top - 1

    def _get_bottom(self):
        return self.top + self.offset_top + self.innerscreen.height + 1

    def _hittest(self, x, y):
        screen = self.innerscreen
        left = self._get_left()
        top = self._get_top()
        if y == top and x >= left and x <= self._get_right():
            return _HITTEST_TITLEBAR
        if x < left:
            return _HITTEST_NONE
        elif x > self._get_right():
            return _HITTEST_NONE
        if y < top:
            return _HITTEST_NONE
        elif y > self._get_bottom():
            return _HITTEST_NONE
        return _HITTEST_CLIENTAREA


class InnerFrame(tff.DefaultHandler,
                 IInnerFrame,
                 IMouseListenerImpl,
                 IFocusListenerImpl): # aggregate mouse and focus listener

    top = 0
    left = 0
    offset_top = 0
    offset_left = 0
    enabled = True

    def __init__(self, session, listener, inputhandler, screen,
                 top, left, row, col,
                 command, termenc, termprop, mousemode):

        innerscreen = Screen(row, col, 0, 0, termenc, termprop)
        canossa = Canossa(innerscreen, visibility=False)

        self._mouse_decoder = MouseDecoder(self, termprop, mousemode)
        self._session = session

        window = screen.create_window(self)
        window.alloc(left - 1, top - 1, col + 2, row + 2)

        self._window = window

        self.top = top
        self.left = left
        self.offset_top = 0
        self.offset_left = 0
        self._termprop = termprop
        self.innerscreen = innerscreen
        self._outerscreen = screen
        self._listener = listener
        self._inputhandler = inputhandler

        session.add_subtty("xterm", "ja_JP.UTF-8",
                           command, row, col, termenc,
                           self, canossa, self)
        self._title = command

    """ tff.EventObserver override """
    def handle_end(self, context):
        self._window.close()
        self._listener.onclose(self, context)

    def handle_csi(self, context, parameter, intermediate, final):
        if self._mouse_decoder.handle_csi(context, parameter, intermediate, final):
            return True
        return True

    def handle_char(self, context, c):
        if self._mouse_decoder.handle_char(context, c):
            return True
        if self._inputhandler.handle_char(context, c):
            return True
        return False

    """ IWidget override """
    def close(self):
        self._session.destruct_subprocess()

    def draw(self, region):
        if self.enabled:
            window = self._window
            screen = self.innerscreen
            left = self.left + self.offset_left
            top = self.top + self.offset_top
            width = screen.width
            height = screen.height

            dirtyregion = region.add(left - 1, top - 1, width + 2, height + 2)
            for index in xrange(0, height):
                dirtyrange = dirtyregion[top + index]
                if dirtyrange:
                    dirty_left = min(dirtyrange)
                    if dirty_left == left - 1:
                        dirty_left = left
                    dirty_right = max(dirtyrange)
                    dirty_width = dirty_right - dirty_left
                    screen.copyrect(window, 0, index, dirty_width, 1,
                                    dirty_left, top + index, lazy=True)
            title_length = self._termprop.wcswidth(self._title)
            width = screen.width + 2
            if title_length < width:
                 pad_left = (width - title_length) / 2
                 pad_right = width - title_length - pad_left
                 title = " " * pad_left + self._title + " " * pad_right
            else:
                 title = self._title[0:width - 3] + "..."

            if self._dragpos:
                window.write("\x1b[30;43m")
            else:
                window.write("\x1b[30;47m")
            window.write("\x1b[%d;%dH" % (top, left))
            window.write(title)
            window.write("\x1b[m")
            for i in xrange(1, screen.height + 1):
                window.write("\x1b[%d;%dH|" % (top + i, left))
                window.write("\x1b[%d;%dH|" % (top + i, left + screen.width + 1))
            window.write("\x1b[%d;%dH" % (top + screen.height + 1, left))
            window.write("+")
            window.write("-" * (screen.width))
            window.write("+")
            cursor = screen.cursor
            window.write("\x1b[?25h")
            window.write("\x1b[%d;%dH" % (cursor.row + top + 1, cursor.col + left + 1))

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

