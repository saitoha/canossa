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

_TITLESTYLE_INACTIVE       = '\x1b[30;47m'
_TITLESTYLE_ACTIVE         = '\x1b[30;42m'
_TITLESTYLE_HOVER          = '\x1b[30;46m'
_TITLESTYLE_DRAG           = '\x1b[30;43m'

_DRAGTYPE_NONE             = 0
_DRAGTYPE_TITLEBAR         = 1
_DRAGTYPE_BOTTOMRIGHT      = 2
_DRAGTYPE_BOTTOMLEFT       = 3

class IFocusListenerImpl(IFocusListener):

    def __init__(self):
        pass

    """ IFocusListener implementation """
    def onfocusin(self):
        #self._session.focus_subprocess()
        #self._window.focus()
        self._titlestyle = _TITLESTYLE_ACTIVE

    def onfocusout(self):
        #self._session.blur_subprocess()
        #self._window.blur()
        self._titlestyle = _TITLESTYLE_INACTIVE
        #self.close()


class IMouseListenerImpl(IMouseListener):

    def __init__(self):
        self._lasthittest = None
        self._dragtype = _DRAGTYPE_NONE
        self._dragpos = None
        self._titlestyle = _TITLESTYLE_INACTIVE

    """ IMouseListener implementation """

    def onmousedown(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            #if self._window.is_active():
            self._window.blur()
            self._session.blur_subprocess()
            #return False
        elif not self._window.is_active():
            self._window.focus()
            self._session.focus_subprocess()
        if hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            x += 33
            y += 33
            if x < 0x80 and y < 0x80:
                context.puts(u'\x1b[M%c%c%c' % (0 + 32, x, y))
        return True

    def onmouseup(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            x += 33
            y += 33
            if x < 0x80 and y < 0x80:
                context.puts(u'\x1b[M%c%c%c' % (3 + 32, x, y))
        return True

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        return True

    def ondoubleclick(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_NONE:
            return False
        return True

    def onmousehover(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            x += 33
            y += 33
            #if x < 0x80 and y < 0x80:
            #    context.puts(u"\x1b[M%c%c%c" % (32 + 32, x, y))
            self._titlestyle = _TITLESTYLE_ACTIVE
        elif hittest == _HITTEST_TITLEBAR:
            self._titlestyle = _TITLESTYLE_HOVER
        elif hittest == _HITTEST_FRAME_BOTTOMLEFT:
            self._titlestyle = _TITLESTYLE_HOVER
        elif hittest == _HITTEST_FRAME_BOTTOMRIGHT:
            self._titlestyle = _TITLESTYLE_HOVER
        else:
            self._titlestyle = _TITLESTYLE_ACTIVE
        return True

    """ scroll """
    def onscrolldown(self, context, x, y):
        hittest = self._lasthittest
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            x += 33
            y += 33
            if x < 0x80 and y < 0x80:
                context.puts(u'\x1b[M%c%c%c' % (64 + 32, x, y))
        return True

    def onscrollup(self, context, x, y):
        hittest = self._lasthittest
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_CLIENTAREA:
            x -= self.left + self.offset_left
            y -= self.top + self.offset_top
            x += 33
            y += 33
            if x < 0x80 and y < 0x80:
                context.puts(u'\x1b[M%c%c%c' % (65 + 32, x, y))
        return True

    """ drag and drop """
    def ondragstart(self, s, x, y):
        #hittest = self._hittest(x, y)
        hittest = self._lasthittest
        #raise Exception([hittest, self._lasthittest, x, y])
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_TITLEBAR:
            self._dragtype = _DRAGTYPE_TITLEBAR
            self._dragpos = (x, y)
            self._titlestyle = _TITLESTYLE_DRAG
        elif hittest == _HITTEST_FRAME_BOTTOMLEFT:
            self._dragtype = _DRAGTYPE_BOTTOMLEFT
            self._titlestyle = _TITLESTYLE_DRAG
        elif hittest == _HITTEST_FRAME_BOTTOMRIGHT:
            self._dragtype = _DRAGTYPE_BOTTOMRIGHT
            self._titlestyle = _TITLESTYLE_DRAG
        return True

    def ondragend(self, s, x, y):
        if self._dragtype == _DRAGTYPE_NONE:
            return False
        self.left += self.offset_left
        self.top += self.offset_top
        self.offset_left = 0
        self.offset_top = 0
        self._dragtype = _DRAGTYPE_NONE
        self._dragpos = None
        self._titlestyle = _TITLESTYLE_ACTIVE
        self._dragstype = _DRAGTYPE_NONE
        return True

    def ondragmove(self, context, x, y):
        if self._dragtype == _DRAGTYPE_NONE:
            return False
        elif self._dragtype == _DRAGTYPE_TITLEBAR:

            assert self._dragpos

            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._outerscreen
            innerscreen = self.innerscreen

            width = innerscreen.width + 2
            height = innerscreen.height + 2

#            if self.left + offset_x - 1 < 0:
#                offset_x = 1 - self.left
#            elif self.left + width + offset_x - 1 > screen.width:
#                offset_x = screen.width - self.left - width + 1
#            if self.top + offset_y - 1 < 0:
#                offset_y = 1 - self.top
#            elif self.top + height + offset_y - 1 > screen.height:
#                offset_y = screen.height - self.top - height + 1

            if self.left + width + offset_x < 1:
                offset_x = 1 - self.left - width
            elif self.left + offset_x > screen.width - 1:
                offset_x = screen.width - self.left - 1
            if self.top + height + offset_y < 1:
                offset_y = 1 - self.top - height
            elif self.top + offset_y > screen.height - 1:
                offset_y = screen.height - self.top - 1

            self.offset_left = offset_x
            self.offset_top = offset_y

            left = self.left + self.offset_left - 1
            top = self.top + self.offset_top - 1
            width = innerscreen.width + 2
            height = innerscreen.height + 2

            self._window.realloc(left, top, width, height)

        elif self._dragtype == _DRAGTYPE_BOTTOMRIGHT:

            screen = self.innerscreen
            window = self._window

            left = self.left
            top = self.top
            row = max(y - top, 5)
            col = max(x - left, 8)

            screen.resize(row, col)
            self._session.subtty.resize(row, col)

            left -= 1
            top -= 1
            width = col + 2
            height = row + 2

            self.width = width
            self.height = height

            window.realloc(left, top, width, height)
        else:
            hittest = self._hittest(x, y)
            self._lasthittest = hittest
            if self._dragtype == _DRAGTYPE_NONE:
                return False
            elif hittest == _HITTEST_CLIENTAREA:
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                x += 33
                y += 33
#                if x < 0x80 and y < 0x80:
#                    context.puts("\x1b[M%c%c%c" % (32 + 32, x, y))
        return True

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
        right = self._get_right()
        bottom = self._get_bottom()
        if x < left:
            return _HITTEST_NONE
        elif x > right - 1:
            return _HITTEST_NONE
        if y < top:
            return _HITTEST_NONE
        elif y > bottom - 1:
            return _HITTEST_NONE
        elif y == top:
            if x >= left and x <= right:
                return _HITTEST_TITLEBAR
        elif y == bottom - 1:
            if x == left:
                return _HITTEST_FRAME_BOTTOMLEFT
            elif x == right - 1:
                return _HITTEST_FRAME_BOTTOMRIGHT
        return _HITTEST_CLIENTAREA


class InnerFrame(tff.DefaultHandler,
                 IInnerFrame,
                 IMouseListenerImpl,
                 IFocusListenerImpl): # aggregate mouse and focus listener

    def __init__(self, session, listener, inputhandler, screen,
                 top, left, row, col,
                 command, termenc, termprop):

        IMouseListenerImpl.__init__(self)
        IFocusListenerImpl.__init__(self)

        self.enabled = True

        innerscreen = Screen(row, col, 0, 0, termenc, termprop)
        canossa = Canossa(innerscreen, visibility=False)

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

        session.add_subtty('xterm', 'ja_JP.UTF-8',
                           command, row, col, termenc,
                           self, canossa, self)
        self._title = command

    """ tff.EventObserver override """
    def handle_end(self, context):
        self._window.close()
        self._listener.onclose(self, context)

    def handle_csi(self, context, parameter, intermediate, final):
        if self._inputhandler.handle_csi(context, parameter, intermediate, final):
            return True
        return False

    def handle_char(self, context, c):
        if self._inputhandler.handle_char(context, c):
            return True
        return False

    def moveto(self, row, col):
        if col >= self._outerscreen.width + 1:
            raise Exception("range error col=%s" % col)
        if row >= self._outerscreen.height + 1:
            raise Exception("range error row=%s" % row)
        if row < 1:
            raise Exception("range error")
        if col < 1:
            raise Exception("range error")
        self._window.write('\x1b[%d;%dH' % (row, col))

    """ IWidget override """
    def draw(self, region):
        if self.enabled:
            window = self._window
            screen = self.innerscreen
            outerscreen = self._outerscreen
            left = self.left + self.offset_left
            top = self.top + self.offset_top
            width = screen.width
            height = screen.height

            dirtyregion = region.add(left - 1, top - 1, width + 2, height + 2)

            # タイトルの描画
            termprop = self._termprop
            title_length = termprop.wcswidth(self._title)
            width = screen.width + 2
            if title_length < width - 10:
                pad_left = (width - title_length) / 2
                pad_right = width - title_length - pad_left
                title = ' ' * pad_left + self._title + ' ' * (pad_right - 2) + u'凶'
            elif width > 10:
                title = '  ' + self._title[0:width - 2 - 8] + u'...   凶'
            else:
                title = ' ' * width

            window.write('\x1b[?25l')
            window.write(self._titlestyle)
            dirtyrange = dirtyregion[top - 1]
            dirty_left = max(max(min(dirtyrange), left - 1), 0)
            dirty_right = min(min(max(dirtyrange) + 1, left + width + 1), outerscreen.width)
            n = left - 1
            for c in title:
                length = termprop.wcwidth(c)
                if n >= dirty_right:
                    break
                if n == dirty_left:
                    self.moveto(top, n + 1)
                if n >= dirty_left:
                    window.write(c)
                n += length

            window.write('\x1b[m')

            # フレーム内容の描画
            for index in xrange(0, height):
                if top + index < outerscreen.height:
                    if top + index >= 0:
                        dirtyrange = dirtyregion[top + index]
                        if dirtyrange:
                            dirty_left = max(min(dirtyrange), 0)
                            if dirty_left == left - 1:
                                dirty_left = left
                            dirty_right = min(max(dirtyrange) + 1, outerscreen.width)
                            dirty_width = dirty_right - dirty_left
                            if left - 1 >= dirty_left - 1:
                                row = top + index + 1
                                col = left
                                self.moveto(row, col)
                                window.write('|')
                            screen.copyrect(window, dirty_left - left, index, dirty_width, 1,
                                            dirty_left, top + index, lazy=True)
                            if left + screen.width < outerscreen.width - 1:
                                row = top + index + 1
                                col = left + screen.width + 1
                                self.moveto(row, col)
                                window.write('|')

            if top + height < outerscreen.height:
                if top + index >= 0:
                    dirtyrange = dirtyregion[top + height]
                    dirty_left = max(max(min(dirtyrange), left - 1), 0)
                    dirty_right = min(min(max(dirtyrange) + 1, left + width + 1), outerscreen.width)
                    window.write('\x1b[m')
                    window.write('\x1b[%d;%dH' % (top + height + 1, left))
                    if left >= dirty_left:
                        window.write('+')
                    for i in xrange(dirty_left, left + width - 3):
                        if i >= dirty_right:
                            break
                        if i >= outerscreen.width:
                            break
                        window.write('-')
                    else:
                        if self._titlestyle == _TITLESTYLE_HOVER:
                            window.write('\x1b[43m')
                        elif self._dragtype == _DRAGTYPE_BOTTOMRIGHT:
                            window.write('\x1b[41m')
                        window.write('+')

            cursor = screen.cursor
            cursor.draw(window)

            window.write('\x1b[?25h'
                         '\x1b[%d;%dH' % (cursor.row + top + 1, cursor.col + left + 1))

    def close(self):
        self._session.destruct_subprocess()


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

