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
from mouse import *
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

class IInnerFrameListener():

    def onclose(self, iframe, context):
        raise NotImplementedError("IInnerFrameListener::onclose")


class IFocusListenerImpl(IFocusListener):

    """ IFocusListener implementation """
    def onfocusin(self):
        pass

    def onfocusout(self):
        pass


class IMouseListenerImpl(IMouseListener):

    _scrollorigin = 0
    _lasthittest = None 
    _dragpos = None

    """ IMouseListener implementation """

    def mouseenabled(self):
        return True 

    def onmousedown(self, context, x, y):
        pass

    def onmouseup(self, context, x, y):
        pass 

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            pass

    def ondoubleclick(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            pass

    def onmousehover(self, context, x, y):
        if self.mouseenabled():
            hittest = self._hittest(x, y)
            if hittest == _HITTEST_CLIENTAREA:
                pass
            elif hittest == _HITTEST_NONE:
                pass

    """ scroll """
    def onscrolldown(self, context, x, y):
        pass

    def onscrollup(self, context, x, y):
        pass

    """ drag and drop """
    def ondragstart(self, s, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_CLIENTAREA:
            pass
        elif hittest == _HITTEST_NONE:
            pass

    def ondragend(self, s, x, y):
        self._dragpos = None
        self._scrollorigin = 0

    def ondragmove(self, context, x, y):
        if self._dragpos:
            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._screen
            if self._left + offset_x < 0:
                offset_x = 0 - self._left
            elif self._left + self._width + offset_x > screen.width:
                offset_x = screen.width - self._left - self._width
            if self._top + offset_y < 0:
                offset_y = 0 - self._top
            elif self._top + self._height + offset_y > screen.height:
                offset_y = screen.height - self._top - self._height

            #s = self._output
            #self._clearDeltaX(s, offset_x)
            #self._clearDeltaY(s, offset_y)

            #self._offset_left = offset_x
            #self._offset_top = offset_y 

    def _hittest(self, x, y):
        if x < self.left:
            return _HITTEST_NONE
        elif x > self.left + self.innerscreen.width:
            return _HITTEST_NONE
        if y < self.top:
            return _HITTEST_NONE
        elif y > self.top + self.innerscreen.height:
            return _HITTEST_NONE
        return _HITTEST_CLIENTAREA

    def _clearDeltaX(self, s, offset_x):
        screen = self._screen
        if self._offset_left < offset_x:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._offset_top,
                            offset_x - self._offset_left,
                            self._height)
        elif self._offset_left > offset_x:
            screen.copyrect(s,
                            self._left + self._width + offset_x,
                            self._top + self._offset_top,
                            self._offset_left - offset_x,
                            self._height)

    def _clearDeltaY(self, s, offset_y):
        screen = self._screen
        if self._offset_top < offset_y:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._offset_top,
                            self._width,
                            offset_y - self._offset_top)
        elif self._offset_top > offset_y:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._height + offset_y,
                            self._width,
                            self._offset_top - offset_y)

class InnerFrame(tff.DefaultHandler,
                 IMouseListenerImpl,
                 IFocusListenerImpl):

    top = 0
    left = 0
    enabled = True

    def __init__(self,
                 session,
                 listener,
                 screen,
                 top,
                 left,
                 row,
                 col,
                 command,
                 termenc,
                 termprop,
                 mousemode):

        innerscreen = Screen(row, col, 0, 0, termenc, termprop)
        canossa = Canossa(innerscreen, visibility=False)

        self._mouse_decoder = MouseDecoder(self, termprop, mousemode)
        self._session = session

        self.top = top
        self.left = left
        self._termprop = termprop
        self.innerscreen = innerscreen
        self._screen = screen
        self._listener = listener

        session.add_subtty("xterm",
                           "ja_JP.UTF-8",
                           command,
                           row, col,
                           termenc,
                           self,
                           canossa,
                           self)
        self._title = command
        session.switch_input_target()

    def handle_end(self, context):
        self._listener.onclose(self, context)

    def handle_csi(self, context, parameter, intermediate, final):
        if self._mouse_decoder.handle_csi(context, parameter, intermediate, final):
            return True
        return True

    def handle_char(self, context, c):
        if self._mouse_decoder.handle_char(context, c):
            return True
        return False

    def close(self):
        self._session.destruct_subprocess()

    def draw(self, output):
        if self.enabled:
            screen = self.innerscreen

            screen.copyrect(output,
                            0, 0,
                            screen.width, screen.height,
                            self.left, self.top)
            title_length = self._termprop.wcswidth(self._title)
            width = screen.width + 2
            if title_length < width:
                 pad_left = (width - title_length) / 2
                 pad_right = width - title_length - pad_left
                 title = " " * pad_left + self._title + " " * pad_right
            else:
                 title = self._title[0:width - 3] + "..."
                       
            output.write("\x1b[30;47m")
            output.write("\x1b[%d;%dH" % (self.top, self.left))
            output.write(title)
            output.write("\x1b[m")
            for i in xrange(1, screen.height + 1):
                output.write("\x1b[%d;%dH|" % (self.top + i, self.left))
                output.write("\x1b[%d;%dH|" % (self.top + i, self.left + screen.width + 1))
            output.write("\x1b[%d;%dH" % (self.top + screen.height + 1, self.left))
            output.write("+")
            output.write("-" * (screen.width))
            output.write("+")
            cursor = screen.cursor
            output.write("\x1b[?25h")
            output.write("\x1b[%d;%dH" % (cursor.row + self.top + 1, cursor.col + self.left + 1))

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

