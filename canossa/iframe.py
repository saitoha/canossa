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
# 
# ***** END LICENSE BLOCK *****


import tff
from constant import *
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
_HITTEST_BUTTON_CLOSE      = 11

_TITLESTYLE_INACTIVE       = '\x1b[30;47m'
_TITLESTYLE_ACTIVE         = '\x1b[30;42m'
_TITLESTYLE_HOVER          = '\x1b[30;46m'
_TITLESTYLE_DRAG           = '\x1b[30;43m'

_DRAGTYPE_NONE             = 0
_DRAGTYPE_TITLEBAR         = 1
_DRAGTYPE_BOTTOMRIGHT      = 2
_DRAGTYPE_BOTTOMLEFT       = 3
_DRAGTYPE_BOTTOM           = 4
_DRAGTYPE_LEFT             = 5
_DRAGTYPE_RIGHT            = 6
_DRAGTYPE_CLIENTAREA       = 7

_HOVERTYPE_NONE            = 0
_HOVERTYPE_TITLEBAR        = 1
_HOVERTYPE_BOTTOMRIGHT     = 2
_HOVERTYPE_BOTTOMLEFT      = 3
_HOVERTYPE_BOTTOM          = 4
_HOVERTYPE_LEFT            = 5
_HOVERTYPE_RIGHT           = 6
_HOVERTYPE_BUTTON_CLOSE    = 7


class IFocusListenerImpl(IFocusListener):

    def __init__(self):
        pass

    """ IFocusListener implementation """
    def onfocusin(self):
        self._titlestyle = _TITLESTYLE_ACTIVE

    def onfocusout(self):
        self._titlestyle = _TITLESTYLE_INACTIVE


class IMouseListenerImpl(IMouseListener):

    def __init__(self):
        self._lasthittest = _HITTEST_NONE
        self._dragtype = _DRAGTYPE_NONE
        self._hovertype = _HOVERTYPE_NONE
        self._dragpos = None
        self._titlestyle = _TITLESTYLE_INACTIVE

    """ IMouseListener implementation """

    def onmousedown(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            #self._window.blur()
            self._session.blur_subprocess()
            return False
        if not self._window.is_active():
            self._window.focus()
            self._session.focus_subprocess(self._tty)
            self._titlestyle = _TITLESTYLE_ACTIVE
            return True
        if hittest == _HITTEST_CLIENTAREA:
            screen = self.innerscreen
            if (screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_BUTTON_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_NORMAL or
                screen.mouse_protocol == MOUSE_PROTOCOL_X10):
                b = 0
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                    x += 33
                    y += 33
                    b += 32
                    if x < 0xff and y < 0xff:
                        context.puts('\x1b[M%c%c%c' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                    x += 33
                    y += 33
                    b += 32
                    context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                    x += 1
                    y += 1
                    context.puts('\x1b[<%d;%d;%dM' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                    x += 1
                    y += 1
                    b += 32
                    context.puts('\x1b[%d;%d;%dM' % (b, x, y))
        return True

    def onmouseup(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        if not self._window.is_active():
            return True
        if hittest == _HITTEST_CLIENTAREA:
            screen = self.innerscreen
            if (screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_BUTTON_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_NORMAL or
                screen.mouse_protocol == MOUSE_PROTOCOL_X10):
                b = 3
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                    x += 33
                    y += 33
                    b += 32
                    if x < 0xff and y < 0xff:
                        context.puts('\x1b[M%c%c%c' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                    x += 33
                    y += 33
                    b += 32
                    context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                    x += 1
                    y += 1
                    context.puts('\x1b[<%d;%d;%dm' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                    x += 1
                    y += 1
                    b += 32
                    context.puts('\x1b[%d;%d;%dM' % (b, x, y))
        return True

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        if hittest == _HITTEST_BUTTON_CLOSE:
            self.close()
            return True
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
            self._hovertype = _HOVERTYPE_NONE
            return False
        if hittest == _HITTEST_CLIENTAREA:
            if self._window.is_active():
                screen = self.innerscreen
                if screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT:
                    b = 32
                    x -= self.left + self.offset_left
                    y -= self.top + self.offset_top
                    if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                        x += 33
                        y += 33
                        b += 32
                        if x < 0xff and y < 0xff:
                            context.puts('\x1b[M%c%c%c' % (b, x, y))
                    elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                        x += 33
                        y += 33
                        b += 32
                        context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                    elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                        x += 1
                        y += 1
                        context.puts('\x1b[<%d;%d;%dM' % (b, x, y))
                    elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                        x += 1
                        y += 1
                        b += 32
                        context.puts('\x1b[%d;%d;%dM' % (b, x, y))
                    self._titlestyle = _TITLESTYLE_ACTIVE
            self._hovertype = _HOVERTYPE_NONE
        elif hittest == _HITTEST_TITLEBAR:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_TITLEBAR
        elif hittest == _HITTEST_FRAME_BOTTOMLEFT:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_BOTTOMLEFT
        elif hittest == _HITTEST_FRAME_BOTTOMRIGHT:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_BOTTOMRIGHT
        elif hittest == _HITTEST_FRAME_BOTTOM:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_BOTTOM
        elif hittest == _HITTEST_FRAME_LEFT:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_LEFT
        elif hittest == _HITTEST_FRAME_RIGHT:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_RIGHT
        elif hittest == _HITTEST_BUTTON_CLOSE:
            self._titlestyle = _TITLESTYLE_HOVER
            self._hovertype = _HOVERTYPE_BUTTON_CLOSE
        else:
            self._titlestyle = _TITLESTYLE_ACTIVE
            self._hovertype = _HOVERTYPE_NONE
        return True

    """ scroll """
    def onscrolldown(self, context, x, y):
        hittest = self._lasthittest
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        if not self._window.is_active():
            return True
        if hittest == _HITTEST_CLIENTAREA:
            screen = self.innerscreen
            if (screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_BUTTON_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_NORMAL):
                b = 64
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                    x += 33
                    y += 33
                    b += 32
                    if x < 0xff and y < 0xff:
                        context.puts('\x1b[M%c%c%c' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                    x += 33
                    y += 33
                    b += 32
                    context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                    x += 1
                    y += 1
                    context.puts('\x1b[<%d;%d;%dM' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                    x += 1
                    y += 1
                    b += 32
                    context.puts('\x1b[%d;%d;%dM' % (b, x, y))
        return True

    def onscrollup(self, context, x, y):
        hittest = self._lasthittest
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        if not self._window.is_active():
            return True
        elif hittest == _HITTEST_CLIENTAREA:
            screen = self.innerscreen
            if (screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_BUTTON_EVENT or
                screen.mouse_protocol == MOUSE_PROTOCOL_NORMAL):
                b = 65
                x -= self.left + self.offset_left
                y -= self.top + self.offset_top
                if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                    x += 33
                    y += 33
                    b += 32
                    if x < 0xff and y < 0xff:
                        context.puts('\x1b[M%c%c%c' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                    x += 33
                    y += 33
                    b += 32
                    context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                    x += 1
                    y += 1
                    context.puts('\x1b[<%d;%d;%dM' % (b, x, y))
                elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                    x += 1
                    y += 1
                    b += 32
                    context.puts('\x1b[%d;%d;%dM' % (b, x, y))
        return True

    """ drag and drop """
    def ondragstart(self, s, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_NONE:
            return False
        if not self._window.is_active():
            return True
        if hittest == _HITTEST_CLIENTAREA:
            self._dragtype = _DRAGTYPE_CLIENTAREA
            self._titlestyle = _TITLESTYLE_ACTIVE
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
        elif hittest == _HITTEST_FRAME_BOTTOM:
            self._dragtype = _DRAGTYPE_BOTTOM
            self._titlestyle = _TITLESTYLE_DRAG
        elif hittest == _HITTEST_FRAME_LEFT:
            self._dragtype = _DRAGTYPE_LEFT
            self._titlestyle = _TITLESTYLE_DRAG
        elif hittest == _HITTEST_FRAME_RIGHT:
            self._dragtype = _DRAGTYPE_RIGHT
            self._titlestyle = _TITLESTYLE_DRAG
        return True

    def ondragend(self, s, x, y):
        hittest = self._lasthittest
        #if hittest == _HITTEST_NONE:
        #    return False
        if self._dragtype == _DRAGTYPE_NONE:
            return True
        if not self._window.is_active():
            return True
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
        hittest = self._lasthittest
        if hittest == _HITTEST_NONE:
            return False
        if self._dragtype == _DRAGTYPE_NONE:
            return False
        if not self._window.is_active():
            return True
        if self._dragtype == _DRAGTYPE_TITLEBAR:

            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._outerscreen
            innerscreen = self.innerscreen

            width = innerscreen.width + 2
            height = innerscreen.height + 2

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
            self._tty.resize(row, col)

            left -= 1
            top -= 1
            width = col + 2
            height = row + 2

            window.realloc(left, top, width, height)

        elif self._dragtype == _DRAGTYPE_BOTTOMLEFT:

            screen = self.innerscreen
            window = self._window

            left = min(max(x, 0), self.left + screen.width - 10)
            top = self.top
            row = max(y - top, 5)
            col = self.left + screen.width - left + 1

            screen.resize(row, col)
            self._tty.resize(row, col)

            left -= 2
            top -= 1
            width = col + 2
            height = row + 2

            self.left = left + 1

            window.realloc(left, top, width, height)

        elif self._dragtype == _DRAGTYPE_BOTTOM:

            screen = self.innerscreen
            window = self._window

            left = self.left
            top = self.top
            row = max(y - top, 5)
            col = screen.width

            screen.resize(row, col)
            self._tty.resize(row, col)

            left -= 1
            top -= 1
            width = col + 2
            height = row + 2

            window.realloc(left, top, width, height)

        elif self._dragtype == _DRAGTYPE_LEFT:

            screen = self.innerscreen
            outerscreen = self._outerscreen
            window = self._window

            left = min(max(x, 0), self.left + screen.width - 10)
            top = self.top
            row = screen.height
            col = self.left + screen.width - left + 1

            left -= 2
            top -= 1
            width = col + 2
            height = row + 2

            if left > outerscreen.width - 1:
                return

            screen.resize(row, col)
            self._tty.resize(row, col)

            self.left = left + 1

            window.realloc(left, top, width, height)

        elif self._dragtype == _DRAGTYPE_RIGHT:

            screen = self.innerscreen
            window = self._window

            left = self.left
            top = self.top
            row = screen.height
            col = max(x - left, 8)

            left -= 1
            top -= 1
            width = col + 2
            height = row + 2

            screen.resize(row, col)
            self._tty.resize(row, col)

            window.realloc(left, top, width, height)

        else:
            hittest = self._hittest(x, y)
            self._lasthittest = hittest
            if hittest == _HITTEST_CLIENTAREA:
                screen = self.innerscreen
                if screen.mouse_protocol == MOUSE_PROTOCOL_ANY_EVENT or screen.mouse_protocol == MOUSE_PROTOCOL_BUTTON_EVENT:
                    b = 32
                    x -= self.left + self.offset_left
                    y -= self.top + self.offset_top
                    if screen.mouse_encoding == MOUSE_ENCODING_NORMAL:
                        x += 33
                        y += 33
                        b += 32
                        if x < 0xff and y < 0xff:
                            context.puts('\x1b[M%c%c%c' % (b, x, y))
                    elif screen.mouse_encoding == MOUSE_ENCODING_UTF8:
                        x += 33
                        y += 33
                        b += 32
                        context.puts(u'\x1b[M%c%c%c' % (unichr(b), unichr(x), unichr(y)))
                    elif screen.mouse_encoding == MOUSE_ENCODING_SGR:
                        x += 1
                        y += 1
                        context.puts('\x1b[<%d;%d;%dM' % (b, x, y))
                    elif screen.mouse_encoding == MOUSE_ENCODING_URXVT:
                        x += 1
                        y += 1
                        b += 32
                        context.puts('\x1b[%d;%d;%dM' % (b, x, y))
        return True

    def _get_left(self):
        return self.left + self.offset_left - self._padding_left

    def _get_right(self):
        return self.left + self.offset_left + self.innerscreen.width + self._padding_right

    def _get_top(self):
        return self.top + self.offset_top - self._padding_top

    def _get_bottom(self):
        return self.top + self.offset_top + self.innerscreen.height + self._padding_bottom

    def _hittest(self, x, y):
        screen = self.innerscreen
        left = self._get_left()
        top = self._get_top()
        right = self._get_right()
        bottom = self._get_bottom()
        if x < left:
            return _HITTEST_NONE
        if x > right - 1:
            return _HITTEST_NONE
        if y < top:
            return _HITTEST_NONE
        if y > bottom - 1:
            return _HITTEST_NONE
        if y == top:
            if x == right - 2:
                return _HITTEST_BUTTON_CLOSE
            if x >= left and x <= right:
                return _HITTEST_TITLEBAR
        if y == bottom - 1:
            if x == left:
                return _HITTEST_FRAME_BOTTOMLEFT
            if x == right - 1:
                return _HITTEST_FRAME_BOTTOMRIGHT
            return _HITTEST_FRAME_BOTTOM
        if x == left:
            return _HITTEST_FRAME_LEFT
        if x == right - 1:
            return _HITTEST_FRAME_RIGHT
        return _HITTEST_CLIENTAREA


class InnerFrame(tff.DefaultHandler,
                 IInnerFrame,
                 IMouseListenerImpl,
                 IFocusListenerImpl): # aggregate mouse and focus listener

    def __init__(self, session, listener, mousedecoder, outerscreen,
                 top, left, row, col,
                 command, termenc, termprop):

        IMouseListenerImpl.__init__(self)
        IFocusListenerImpl.__init__(self)

        self.enabled = True

        innerscreen = Screen(row, col, 0, 0, termenc, termprop)
        canossa = Canossa(innerscreen, visibility=False)

        self._session = session

        self._padding_top = 1
        self._padding_left = 1
        self._padding_bottom = 1
        self._padding_right = 1

        window = outerscreen.create_window(self)
        window.alloc(left - self._padding_left,
                     top - self._padding_top,
                     col + self._padding_left + self._padding_right,
                     row + self._padding_top + self._padding_bottom)
        window.focus()

        self._window = window

        mousedecoder.initialize_mouse(window)

        self._mousedecoder = mousedecoder

        self.left = window.left + self._padding_left
        self.top = window.top + self._padding_top
        self.offset_top = 0
        self.offset_left = 0

        self._termprop = termprop
        self.innerscreen = innerscreen
        self._outerscreen = outerscreen
        self._listener = listener
        self._mousedecoder = mousedecoder

        self._tty = session.add_subtty('xterm', 'ja_JP.UTF-8',
                                       command, row, col, termenc,
                                       self, canossa, self)
        self._title = command

    """ tff.EventObserver override """
    def handle_end(self, context):
        outerscreen = self._outerscreen
        self._window.close()
        self._listener.onclose(self, context)
        outerscreen.setfocus()
        if not outerscreen.has_visible_windows():
            self._mousedecoder.uninitialize_mouse(self._window)

    def handle_csi(self, context, parameter, intermediate, final):
        if self._mousedecoder.handle_csi(context, parameter, intermediate, final):
            return True
        return False

    def handle_char(self, context, c):
        if self._mousedecoder.handle_char(context, c):
            return True
        return False

    def moveto(self, row, col):
        outerscreen = self._outerscreen
        if col >= outerscreen.width + 1:
            raise Exception("range error col=%s" % col)
        if row >= outerscreen.height + 1:
            raise Exception("range error row=%s" % row)
        if row < 1:
            raise Exception("range error row=%s" % row)
        if col < 1:
            raise Exception("range error col=%s" % col)
        self._window.write('\x1b[%d;%dH' % (row, col))

    def _drawtitle(self, dirtyregion):
        window = self._window
        innerscreen = self.innerscreen
        outerscreen = self._outerscreen
        left = self.left + self.offset_left
        top = self.top + self.offset_top

        # draw the title bar
        termprop = self._termprop
        innertitle = innerscreen.gettitle()
        if innertitle:
            self._title = innertitle
        title_length = termprop.wcswidth(self._title)
        width = innerscreen.width + self._padding_left + self._padding_right
        if title_length < width - 11:
            pad_left = (width - title_length) / 2
            pad_right = width - title_length - pad_left
            title = u' ' * pad_left + self._title + u' ' * (pad_right - 3) + u'[x]'
        elif width > 10:
            title = u'  ' + self._title[0:width - 2 - 9] + u'...   [x]'
        else:
            title = u' ' * (width - 3) + u'[x]'

        window.write(self._titlestyle)
        dirtyrange = dirtyregion[top - 1]

        if not dirtyrange:
            return

        dirty_left = min(dirtyrange)
        if dirty_left < left - 1:
            dirty_left = left - 1
        if dirty_left < 0:
            dirty_left = 0

        dirty_right = max(dirtyrange) + 1
        if dirty_right > left + innerscreen.width + 1:
            dirty_right = left + innerscreen.width + 1
        if dirty_right > outerscreen.width:
            dirty_right = outerscreen.width

        n = left - 1

        for c in title:
            length = termprop.wcwidth(ord(c))
            if n >= outerscreen.width:
                break
            if n >= dirty_right:
                break
            if n == dirty_left and top > 0:
                self.moveto(top, n + 1)
            if n >= dirty_left:
                if n in dirtyrange:
                    if n == left + width - 4 and self._hovertype == _HOVERTYPE_BUTTON_CLOSE:
                        window.write('\x1b[37m')
                    window.write(c)
                else:
                    window.write("\x1b[%dC" % length)
            n += length

    def _drawbottom(self, dirtyregion):
        window = self._window
        innerscreen = self.innerscreen
        outerscreen = self._outerscreen
        left = self.left + self.offset_left
        top = self.top + self.offset_top

        # draw the bottom of frame
        bottom = top + innerscreen.height - 1 + self._padding_bottom
        if bottom < outerscreen.height:
            if top + innerscreen.height >= 0:

                dirtyrange = dirtyregion[bottom]

                if dirtyrange:
                    dirty_left = min(dirtyrange)
                    if dirty_left < left - 1:
                        dirty_left = left - 1
                    if dirty_left < 0:
                        dirty_left = 0

                    dirty_right = max(dirtyrange) + 1
                    if dirty_right > left + innerscreen.width + 1:
                        dirty_right = left + innerscreen.width + 1
                    if dirty_right > outerscreen.width:
                        dirty_right = outerscreen.width

                    window.write('\x1b[m')
                    self.moveto(bottom + 1, dirty_left + 1)

                    n = left - 1
                    if n >= 0 and n >= dirty_left:
                        if self._dragtype == _DRAGTYPE_BOTTOMLEFT:
                            window.write('\x1b[41m')
                        elif self._hovertype == _HOVERTYPE_BOTTOMLEFT:
                            window.write('\x1b[43m')
                        else:
                            window.write('\x1b[m')
                        window.write('+')
                        n += 1

                    if self._dragtype == _DRAGTYPE_BOTTOM:
                        window.write('\x1b[41m')
                    elif self._hovertype == _HOVERTYPE_BOTTOM:
                        window.write('\x1b[43m')
                    else:
                        window.write('\x1b[m')
                    while True:
                        if n >= dirty_right - 1:
                            if n == left + innerscreen.width:
                                if self._dragtype == _DRAGTYPE_BOTTOMRIGHT:
                                    window.write('\x1b[41m')
                                elif self._hovertype == _HOVERTYPE_BOTTOMRIGHT:
                                    window.write('\x1b[43m')
                                else:
                                    window.write('\x1b[m')
                                window.write('+')
                            break
                        if n >= outerscreen.width:
                            break
                        n += 1
                        if n < dirty_left + 1:
                            continue
                        window.write('-')

    def _drawsideframe(self, dirtyregion):
        window = self._window
        innerscreen = self.innerscreen
        outerscreen = self._outerscreen
        left = self.left + self.offset_left
        top = self.top + self.offset_top


        for index in xrange(0, innerscreen.height):
            if top + index < outerscreen.height:
                if top + index >= 0:
                    dirtyrange = dirtyregion[top + index]
                    if dirtyrange:

                        dirty_left = min(dirtyrange)
                        if dirty_left < 0:
                            dirty_left = 0
                        if dirty_left < left:
                            dirty_left = left

                        dirty_right = max(dirtyrange)
                        if dirty_right > outerscreen.width:
                            dirty_right = outerscreen.width
                        if dirty_right > left + innerscreen.width + 1:
                            dirty_right = left + innerscreen.width + 1

                        dirty_width = dirty_right - dirty_left
                        if dirty_width < 0:
                            continue

                        # draw the left edge of frame
                        if left > 0 and left >= dirty_left and left - 1 < outerscreen.width:
                            row = top + index
                            col = left - 1
                            self.moveto(row + 1, col + 1)

                            if self._dragtype == _DRAGTYPE_LEFT:
                                window.write('\x1b[41m')
                            elif self._hovertype == _HOVERTYPE_LEFT:
                                window.write('\x1b[43m')
                            else:
                                window.write('\x1b[m')
                            window.write('|')
                            window.write('\x1b[m')

                        # draw the right edge of frame
                        col = left + innerscreen.width
                        if col <= dirty_right and col < outerscreen.width:
                            row = top + index
                            self.moveto(row + 1, col + 1)

                            if self._dragtype == _DRAGTYPE_RIGHT:
                                window.write('\x1b[41m')
                            elif self._hovertype == _HOVERTYPE_RIGHT:
                                window.write('\x1b[43m')
                            else:
                                window.write('\x1b[m')
                            window.write('|')
                            window.write('\x1b[m')

    def _drawcontent(self, dirtyregion):
        window = self._window
        innerscreen = self.innerscreen
        outerscreen = self._outerscreen
        left = self.left + self.offset_left
        top = self.top + self.offset_top

        #innerscreen.copyrect(window, 0, 0, innerscreen.width, innerscreen.height, left, top, lazy=True)
        # draw the inner content of frame
        for index in xrange(0, innerscreen.height):
            if top + index < outerscreen.height:
                if top + index >= 0:
                    dirtyrange = dirtyregion[top + index]
                    if dirtyrange:

                        dirty_left = min(dirtyrange)
                        if dirty_left < 0:
                            dirty_left = 0
                        if dirty_left < left:
                            dirty_left = left

                        dirty_right = max(dirtyrange)
                        if dirty_right > outerscreen.width:
                            dirty_right = outerscreen.width
                        if dirty_right > left + innerscreen.width + 1:
                            dirty_right = left + innerscreen.width + 1

                        dirty_width = dirty_right - dirty_left
                        if dirty_width < 0:
                            continue

                        innerscreen.copyrect(window,
                                             dirty_left - left,
                                             index,
                                             dirty_width,
                                             1,
                                             dirty_left,
                                             top + index,
                                             lazy=True)


    def _drawcursor(self):
        window = self._window
        innerscreen = self.innerscreen
        outerscreen = self._outerscreen
        left = self.left + self.offset_left
        top = self.top + self.offset_top
        if window.is_active():
            cursor = innerscreen.cursor
            row = cursor.row + top
            if row < 1:
                return
            elif row >= outerscreen.width:
                return
            col = cursor.col + left
            if col < 1:
                return
            elif col >= outerscreen.width:
                return
            if row < 1:
                return
            elif row >= outerscreen.height:
                return
            self.moveto(row + 1, col + 1)
            window.write('\x1b[?25h')

    """ IWidget override """
    def draw(self, region):
        if self.enabled:
            window = self._window
            innerscreen = self.innerscreen
            outerscreen = self._outerscreen
            left = self.left + self.offset_left
            top = self.top + self.offset_top
            width = innerscreen.width
            height = innerscreen.height

            dirtyregion = region.add(left - self._padding_left,
                                     top - self._padding_top,
                                     width + self._padding_left + self._padding_right,
                                     height + self._padding_top + self._padding_bottom)

            window.write('\x1b[?25l')
            window.write('\x1b[m')

            self._drawcontent(dirtyregion)
            self._drawtitle(dirtyregion)
            self._drawbottom(dirtyregion)
            self._drawsideframe(dirtyregion)
            self._drawcursor()

    def close(self):
        session = self._session
        outerscreen = self._outerscreen
        fd = self._tty.fileno()
        session.destruct_subprocess(fd)
        outerscreen.setfocus()
        if not outerscreen.has_visible_windows():
            self._mousedecoder.uninitialize_mouse(self._window)


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
