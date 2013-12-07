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


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import codecs
from interface import IScreen
from constant import *


#
# CSI ... ; ... R
#
from cursor import Cursor
from line import Line
from mouse import IFocusListener, IMouseListener, MouseDecoder


class IFocusListenerImpl(IFocusListener):

    def __init__(self):
        pass

    """ IFocusListener implementation """
    def onfocusin(self):
        pass

    def onfocusout(self):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            widget.onfocusout()


class IMouseListenerImpl(IMouseListener):

    def __init__(self):
        pass

    """ IMouseListener implementation """
    def onmousedown(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onmousedown(context, x, y):
                return True
        return False

    def onmouseup(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onmouseup(context, x, y):
                return True
        return False

    def onclick(self, context, x, y):
        widgets = self._widgets
        self._active = False
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onclick(context, x, y):
                return True
        for window in self._layouts:
            window.blur()
        self._active = True
        return False

    def ondoubleclick(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.ondoubleclick(context, x, y):
                return True
        return False

    def onmousehover(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onmousehover(context, x, y):
                return True
        return False

    """ scroll """
    def onscrolldown(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onscrolldown(context, x, y):
                return True
        return False

    def onscrollup(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.onscrollup(context, x, y):
                return True
        return False

    """ drag and drop """
    def ondragstart(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.ondragstart(context, x, y):
                return True
        return False

    def ondragend(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.ondragend(context, x, y):
                return True
        return False

    def ondragmove(self, context, x, y):
        widgets = self._widgets
        for window in self._layouts:
            widget = widgets[window.id]
            if widget.ondragmove(context, x, y):
                return True
        return False


class SupportsDoubleSizedTrait():

    def decdhlt(self):
        line = self.lines[self.cursor.row]
        line.set_dhlt()

    def decdhlb(self):
        line = self.lines[self.cursor.row]
        line.set_dhlb()

    def decswl(self):
        line = self.lines[self.cursor.row]
        line.set_swl()

    def decdwl(self):
        line = self.lines[self.cursor.row]
        line.set_dwl()


class SuuportsCursorPersistentTrait():

    def save_pos(self):
        self._saved_pos = (self.cursor.row, self.cursor.col)

    def restore_pos(self):
        if self._saved_pos:
            self.cursor.row, self.cursor.col = self._saved_pos


class SuuportsISO2022DesignationTrait():

    __g = None
    __gl = None

    def _setup_charset(self):
        self.__g = [0x42, 0x30, 0x42, 0x42]
        self.__gl = self.__g[0]

    def set_g0(self, c):
        self.__g[0] = c
        self.cursor.attr.set_charset(c)

    def set_g1(self, c):
        self.__g[1] = c
        self.cursor.attr.set_charset(c)

    def so(self):
        self.__gl = self.__g[1]
        self.cursor.attr.set_charset(self.__gl)

    def si(self):
        self.__gl = self.__g[0]
        self.cursor.attr.set_charset(self.__gl)


class SuuportsAlternateScreenTrait():

    def _setup_altbuf(self):
        self._altbuf = [Line(self.width) for line in xrange(0, self.height)]
        self._mainbuf = self.lines

    def switch_mainbuf(self):
        self.lines = self._mainbuf
        bcevalue = self.cursor.attr.getbcevalue()
        for line in self.lines:
            line.clear(bcevalue)
        lines = self.lines
        if len(lines) > self.height:
            while len(lines) != self.height:
                lines.pop()
            for line in lines:
                line.resize(self.width)
        elif len(lines) < self.height:
            for line in lines:
                line.resize(self.width)
            while len(lines) < self.height:
                lines.insert(0, Line(self.width))
        else:
            for line in lines:
                line.resize(self.width)
        assert len(lines) == self.height
        for line in lines:
            assert self.width == line.length()

    def switch_altbuf(self):
        self.lines = self._altbuf
        bcevalue = self.cursor.attr.getbcevalue()
        for line in self.lines:
            line.clear(bcevalue)
        lines = self.lines
        if len(lines) > self.height:
            while len(lines) > self.height:
                lines.pop()
            for line in lines:
                line.resize(self.width)
        elif len(lines) < self.height:
            for line in lines:
                line.resize(self.width)
            while len(lines) < self.height:
                lines.insert(0, Line(self.width))
        else:
            for line in lines:
                line.resize(self.width)
        assert len(lines) == self.height
        for line in lines:
            assert self.width == line.length()


class SupportsAnsiModeTrait():
    pass


class SupportsExtendedModeTrait():

    dectcem = True
    decawm = True
    decom = False
    allow_deccolm = False

    mouse_protocol = MOUSE_PROTOCOL_NONE 
    mouse_encoding = MOUSE_ENCODING_NORMAL 

    def decset(self, params):
        for param in params:
            if param == 25:
                self.dectcem = True
            elif param == 3:
                if self.allow_deccolm:
                    self.resize(self.height, 132)
                    self.ris()
            elif param == 6:
                self.decom = True
            elif param == 7:
                self.decawm = True
            elif param == 9:
                self.mouse_protocol = MOUSE_PROTOCOL_X10
            elif param == 40:
                self.allow_deccolm = True
            elif param == 1000:
                self.mouse_encoding = MOUSE_ENCODING_NORMAL
                self.mouse_protocol = MOUSE_PROTOCOL_NORMAL
            elif param == 1001:
                self.mouse_protocol = MOUSE_PROTOCOL_HIGHLIGHT
            elif param == 1002:
                self.mouse_protocol = MOUSE_PROTOCOL_BUTTON_EVENT
            elif param == 1003:
                self.mouse_protocol = MOUSE_PROTOCOL_ANY_EVENT
            elif param == 1005:
                self.mouse_encoding = MOUSE_ENCODING_UTF8
            elif param == 1006:
                self.mouse_encoding = MOUSE_ENCODING_SGR
            elif param == 1015:
                self.mouse_encoding = MOUSE_ENCODING_URXVT
            elif param == 1047:
                self.switch_altbuf()
                return True
            elif param == 1048:
                self.save_pos()
                return True
            elif param == 1049:
                self.save_pos()
                self.switch_altbuf()
                return True
        return False

    def decrst(self, params):
        for param in params:
            if param == 25:
                self.dectcem = False
            elif param == 3:
                if self.allow_deccolm:
                    self.resize(self.height, 80)
                    self.ris()
            elif param == 6:
                self.decom = False
            elif param == 7:
                self.decawm = False
            elif param == 9:
                self.mouse_protocol = MOUSE_PROTOCOL_NONE
            elif param == 40:
                self.allow_deccolm = False
            elif param == 1000:
                self.mouse_protocol = MOUSE_PROTOCOL_NONE
            elif param == 1001:
                self.mouse_protocol = MOUSE_PROTOCOL_NONE
            elif param == 1002:
                self.mouse_protocol = MOUSE_PROTOCOL_NONE
            elif param == 1003:
                self.mouse_protocol = MOUSE_PROTOCOL_NONE
            elif param == 1005:
                self.mouse_encoding = MOUSE_ENCODING_NORMAL
            elif param == 1006:
                self.mouse_encoding = MOUSE_ENCODING_NORMAL
            elif param == 1015:
                self.mouse_encoding = MOUSE_ENCODING_NORMAL
            elif param == 1047:
                self.switch_mainbuf()
                return True
            elif param == 1048:
                self.restore_pos()
                return True
            elif param == 1049:
                self.switch_mainbuf()
                self.restore_pos()
                return True
        return False

    def xt_save(self, params):
        pass

    def xt_rest(self, params):
        pass


class SupportsTabStopTrait():

    _tabstop = None

    def _setup_tab(self):
        self._tabstop = [n for n in xrange(0, self.width + 1, 8)]

    def hts(self):
        if self.cursor.col in self._tabstop:
            pass
        elif len(self._tabstop) > 0 and self._tabstop[0] > self.cursor.col:
            self._tabstop.insert(0, self.cursor.col)
        else:
            for i, stop in enumerate(self._tabstop[0:]):
                if self.cursor.col < stop:
                    self._tabstop.insert(i, self.cursor.col)
                    break
            else:
                self._tabstop.append(self.cursor.col)

    def tbc(self, ps):
        if ps == 0:
            if self.cursor.col in self._tabstop:
                self._tabstop.remove(self.cursor.col)
        elif ps == 3:
            self._tabstop = []

    def ht(self):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        line = self.lines[cursor.row]
        col = self.cursor.col
        if line.is_normal():
            if len(self._tabstop) > 0:
                max_pos = self._tabstop[-1]
            else:
                max_pos = 0
        else:
            max_pos = self.width / 2 - 1
        if col < self.width:
            col += 1
            for stop in self._tabstop:
                if col <= stop:
                    if stop >= max_pos:
                        cursor.col = max_pos
                    else:
                        cursor.col = stop
                    break
            else:
                self.cursor.col = self.width - 1
        else:
            self.cursor.col = 0
        self.cursor.dirty = True


class CanossaRangeException(Exception):
    ''' thrown when an invalid range is detected '''

    def __init__(self, message):
        """
        >>> e = CanossaRangeException("test1")
        >>> e.message
        'test1'
        """
        self.message = message

    def __str__(self):
        """
        >>> e = CanossaRangeException("test2")
        >>> e.message
        'test2'
        """
        return repr(self.message)


class IScreenImpl(IScreen):

    _listener = None

    def copyline(self, s, x, y, length, lazy=False):
        if not lazy or line.dirty:
            try:
                if x + length > self.width:
                    raise CanossaRangeException("x + length = %d" % (x + length))
                elif x < 0:
                    raise CanossaRangeException("x = %d" % x)
                if y >= self.height:
                    raise CanossaRangeException("y = %d" % y)
                elif y < 0:
                    raise CanossaRangeException("y = %d" % y)

                assert self.height == len(self.lines)
                assert y < self.height
            except e:
                import logging
                logging.exception(e)
                return

            cursor = Cursor(0, 0)
            cursor.attr.draw(s)
            while True:
                s.write("\x1b[%d;%dH" % (y + 1, x + 1))
                line = self.lines[y]
                if x + length < self.width:
                    line.drawrange(s, x, x + length, cursor)
                    break
                line.drawrange(s, x, self.width - x, cursor)
                length -= self.width - x
                if length <= 0:
                    break
                if y < self.height - 1:
                    break
                x = 0
                if self.decawm:
                    y += 1
            self.cursor.attr.draw(s)

    def copyrect(self, s, srcx, srcy, width, height,
                 destx=None, desty=None, lazy=False):
        if destx is None:
            destx = srcx
        if desty is None:
            desty = srcy

        #if destx < 0:
        #    destx = 0
        #if desty < 0:
        #    desty = 0
        #height = min(height, (self.height - 1) - desty)
        #width =  min(width, (self.width - 1) - destx)
        #if srcx < 0:
        #    srcx = 0
        #if srcy < 0:
        #    srcy = 0
        if srcx < 0 or srcy < 0 or height < 0 or width < 0:
            template = "invalid rect is detected. (%d, %d, %d, %d)"
            message = template % (srcx, srcy, width, height)
            raise CanossaRangeException(message)
        if srcx + width > self.width:
            raise CanossaRangeException("srcx + width = %d; self.width = %d" % (srcx + width, self.width))
        elif srcx < 0:
            raise CanossaRangeException("srcx = %d" % x)
        if srcy + height > self.height:
            raise CanossaRangeException("srcy + height = %d; self.height = %d" % (srcy + height, self.height))
        elif srcy < 0:
            raise CanossaRangeException("srcy = %d" % y)

        cursor = Cursor(0, 0, self.cursor.attr)
        cursor.attr.draw(s)
        for i in xrange(srcy, srcy + height):
            if i >= self.height:
                break
            line = self.lines[i]
            if not lazy or line.dirty:
                s.write("\x1b[%d;%dH" % (desty - srcy + i + 1, destx + 1))
                line.drawrange(s, srcx, srcx + width, cursor, lazy)

        self._region.sub(srcx, srcy, width, height)

    def getyx(self):
        cursor = self.cursor
        return cursor.row, cursor.col

    def drawall(self, context):
        s = self._output
        cursor = Cursor(0, 0)
        cursor.attr.draw(s)
        for i in xrange(0, self.height):
            s.write("\x1b[%d;1H" % (i + 1))
            line = self.lines[i]
            line.drawall(s, cursor)
        self.cursor.draw(s)
        self.cursor.attr.draw(s)
        context.puts(s.getvalue())
        s.truncate(0)

    def drawwindows(self, context):
        trash = self._trash
        if trash:
            for window in trash:
                window.dealloc()
                window.draw(context)
            del trash[:]
        region = self._region
        widgets = self._widgets
        region.reset()
        for window in self._layouts:
            widget = widgets[window.id]
            widget.draw(region)
        for window in reversed(self._layouts):
            widget = widgets[window.id]
            window.draw(context)

    def resize(self, row, col):
        lines = self.lines
        height = len(lines)
        assert self.height == len(lines)
        if row < height:
            while row != len(lines):
                lines.pop()
            for line in lines:
                line.resize(col)
        elif row != height:
            for line in lines:
                line.resize(col)
            while row > len(lines):
                lines.insert(0, Line(col))
        else:
            for line in lines:
                line.resize(col)
        assert row == len(lines)
        for line in lines:
            assert col == line.length()
        if self.scroll_top == 0 and self.scroll_bottom == self.height:
            self.scroll_top = 0
            self.scroll_bottom = row
        self.height = row
        self.width = col
        assert self.height == len(self.lines)
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        self._setup_tab()

    def adjust_cursor(self):
        pos = self._termprop.getyx()
        cursor = self.cursor
        if pos != (0, 0):
            row, col = pos
            cursor.row, cursor.col = row - 1, col - 1
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1

    def sp(self):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1

        row, col = cursor.row, cursor.col
        line = self.lines[row]

        width = self.width
        if col >= width:
            if self.decawm:
                self._wrap()
                row, col = cursor.row, cursor.col
                line = self.lines[row]
            else:
                col = width - 1

        line.dirty = True

        if col >= width:
            col = width - 1
            cursor.col = col
        line.write(0x20, col, cursor.attr)
        cursor.dirty = True
        cursor.col += 1

    def write(self, c):
        cursor = self.cursor
        row, col = cursor.row, cursor.col
        line = self.lines[row]
        width = self.width
        if c < 0xff:
            if col >= width:
                if self.decawm:
                    self._wrap()
                    row, col = cursor.row, cursor.col
                    line = self.lines[row]
                else:
                    col = width - 1
                    cursor.col = col
            line.write(c, col, cursor.attr)
            cursor.dirty = True
            cursor.col += 1
        else:
            char_width = self._wcwidth(c)
            if col >= width - char_width + 1:
                if self.decawm:
                    self._wrap()
                    row, col = cursor.row, cursor.col
                    line = self.lines[row]
                else:
                    col = width - char_width
                    cursor.col = col
            if char_width == 1:  # normal (narrow) character
                line.write(c, col, cursor.attr)
                cursor.dirty = True
                cursor.col += 1
            elif char_width == 2:  # wide character
                line.pad(col)
                line.write(c, col + 1, cursor.attr)
                cursor.dirty = True
                cursor.col += 2
            elif char_width == 0:  # combining character
                if not self._termprop is None:
                    if not self._termprop.has_combine:
                        line.write(c, col, cursor.attr)
                        cursor.dirty = True
                        cursor.col += 1
                line.combine(c, col)

    def setlistener(self, listener):
        self._listener = listener


class MockScreen():

    width = 80
    height = 24

    def __init__(self, row=24, col=80):
        self.height = row
        self.width = col
        self._setup_lines()

    def _setup_lines(self):
        self.lines = [Line(self.width) for line in xrange(0, self.height)]


class MockScreenWithCursor(MockScreen):

    width = 80
    height = 24

    def __init__(self, row=24, col=80, y=0, x=0):
        self.height = row
        self.width = col
        self.cursor = Cursor(y, x)
        self._setup_lines()

class MockScreenWithWindows(MockScreen):

    width = 80
    height = 24
    scroll_top = 0
    scroll_bottom = 24

    def __init__(self, row=24, col=80, y=0, x=0):
        self.height = row
        self.width = col
        self.cursor = Cursor(y, x)
        self._setup_lines()

    def has_visible_windows(self):
        return True

    def drawall(self, context):
        pass

    def drawwindows(self, context):
        pass

class Window():

    _counter = 0

    def __init__(self, screen):
        writer = codecs.getwriter(screen.termenc)
        stream = StringIO()
        self._buffer = writer(stream, errors='ignore')
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self._show = False
        self.__class__._counter += 1
        self.id = self.__class__._counter
        self._screen = screen

    def alloc(self, left, top, width, height):
        self._show = True
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def realloc(self, left, top, width, height):
        screen = self._screen
        if self.left < left:
            x = max(self.left, 0)
            y = max(self.top, 0)
            w = min(left - self.left, screen.width - x)
            h = min(self.height, screen.height - y)
            screen.copyrect(self, x, y, w, h)
        if self.left + self.width > left + width:
            if screen.width > left + width:
                x = left + width
                y = max(self.top, 0)
                w = min((self.left + self.width) - (left + width), screen.width - x)
                h = min(self.height, screen.height - y)
                screen.copyrect(self, x, y, w, h)
        if self.top + self.height > top + height:
            if screen.height > top + height:
                x = max(self.left, 0)
                y = top + height
                w = min(self.width, screen.width - x)
                h = min(self.top + self.height - (top + height), screen.height - y)
                screen.copyrect(self, x, y, w, h)
        if self.top < top:
            x = max(self.left, 0)
            y = max(self.top, 0)
            w = min(self.width, screen.width - x)
            h = top - self.top
            screen.copyrect(self, x, y, w, h)
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def dealloc(self):
        self._show = False

        screen = self._screen
        left = max(self.left, 0)
        top = max(self.top, 0)
        width = min(self.width, screen.width - left)
        height = min(self.height, screen.height - top)
        screen.copyrect(self, left, top, width, height)

        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0

    def write(self, s):
        self._buffer.write(s)

    def is_shown(self):
        return self._show

    def draw(self, context):
        buffer = self._buffer
        s = self._buffer.getvalue()
        if s:
            context.puts(s)
            buffer.truncate(0)

    def focus(self):
        self._screen.focus(self)

    def blur(self):
        self._screen.blur(self)

    def is_active(self):
        return self._screen.is_active(self)

    def close(self):
        self._screen.destruct_window(self)


class Ranges():

    def __init__(self):
        self._ranges = set()

    def add(self, start, end):
        ranges = self._ranges
        newrange = set(xrange(start, end))
        dirtyrange = newrange.difference(ranges)
        ranges.update(newrange)
        return dirtyrange

    def sub(self, start, end):
        ranges = self._ranges
        newrange = set(xrange(start, end))
        ranges.difference_update(newrange)


class Region():

    def __init__(self):
        self._lines = {}

    def add(self, left, top, width, height):
        lines = self._lines
        result = {}
        for index in xrange(top, top + height):
            if not index in lines:
                line = Ranges()
                lines[index] = line
            else:
                line = lines[index]
            dirtyrange = line.add(left, left + width)
            result[index] = dirtyrange
        return result

    def sub(self, left, top, width, height):
        lines = self._lines
        for index in xrange(top, top + height):
            if index in lines:
                line = lines[index]
                dirtyrange = line.sub(left, left + width)

    def reset(self):
        self._lines = {}


class Screen(IScreenImpl,
             IFocusListenerImpl,
             IMouseListenerImpl,
             MockScreenWithCursor,
             SupportsAnsiModeTrait,
             SupportsExtendedModeTrait,
             SupportsTabStopTrait,
             SupportsDoubleSizedTrait,
             SuuportsCursorPersistentTrait,
             SuuportsAlternateScreenTrait,
             SuuportsISO2022DesignationTrait):

    parent = None

    def __init__(self, row=24, col=80, y=0, x=0,
                 termenc="UTF-8", termprop=None):

        self._saved_pos = None
        self._title = u""
        self._widgets = None

        self.height = row
        self.width = col
        self.cursor = Cursor(y, x)
        self.scroll_top = 0
        self.scroll_bottom = self.height
        self.termenc = termenc
        self._output = codecs.getwriter(termenc)(StringIO())
        self._active = True

        if termprop is None:
            from termprop import Termprop
            termprop = Termprop()

        self._wcwidth = termprop.wcwidth
        self._termprop = termprop

        self._setup_lines()
        self._setup_altbuf()
        self._setup_tab()
        self._setup_charset()

        self._widgets = {}
        self._layouts = []
        self._trash = []

        self._region = Region()

    def create_window(self, widget):
        window = Window(self)
        self._widgets[window.id] = widget
        self._layouts.insert(0, window)
        return window

    def focus(self, window):
        layouts = self._layouts
        layouts.remove(window)
        layouts.insert(0, window)
        self._active = False

    def blur(self, window):
        layouts = self._layouts
        layouts.remove(window)
        layouts.append(window)
        if len(layouts) < 2:
            self._active = True

    def is_active(self, window):
        layouts = self._layouts
        if layouts:
            return layouts[0] == window
        return False

    def has_active_windows(self):
        return not self._active

    def setfocus(self):
        self._active = True

    def has_visible_windows(self):
        for window in self._layouts:
            if window.is_shown():
                return True
        return False

    def destruct_window(self, window):
        widgets = self._widgets
        layouts = self._layouts
        if window.id in widgets:
            del widgets[window.id]
        if window in layouts:
            layouts.remove(window)
        self._trash.append(window)

    def _wrap(self):
        self.cursor.col = 0
        self.lf()

    def settitle(self, s):
        if self._listener:
            s = self._listener.ontitlechanged(s)
        self._title = s

    def gettitle(self):
        return self._title

    def bs(self):
        if self.cursor.col >= self.width:
            self.cursor.col = self.width - 1
        if self.cursor.col <= 0:
            pass  # TODO: reverse wrap
        else:
            self.cursor.col -= 1
        self.cursor.dirty = True

    def lf(self):
        cursor = self.cursor
        if cursor.col < self.width:
            #if self.cursor.col >= self.width:
            #    if self.decawm:
            #        self._wrap()
            cursor.row += 1
            if cursor.row >= self.scroll_bottom:
                bcevalue = cursor.attr.getbcevalue()
                for line in self.lines[self.scroll_top + 1:self.scroll_bottom]:
                    line.dirty = True
                line = self.lines.pop(self.scroll_top)
                line.clear(bcevalue)
                self.lines.insert(self.scroll_bottom - 1, line)
                cursor.row = self.scroll_bottom - 1
            cursor.dirty = True

    def ind(self):
        self.lf()

    def nel(self):
        self.cr()
        self.lf()

    def ri(self):
        cursor = self.cursor
        if cursor.row <= self.scroll_top:
            bcevalue = cursor.attr.getbcevalue()
            for line in self.lines:
                line.dirty = True
            line = self.lines.pop(self.scroll_bottom - 1)
            line.clear(bcevalue)
            self.lines.insert(self.scroll_top, line)
            cursor.row = self.scroll_top
        else:
            cursor.row -= 1
        cursor.dirty = True

    def cr(self):
        self.cursor.col = 0
        self.cursor.dirty = True

    def decstbm(self, top, bottom):
        self.scroll_top = max(0, top)
        self.scroll_bottom = min(bottom + 1, self.height)
        self.cursor.row = self.scroll_top
        self.cursor.col = 0

    def dch(self, n):
        self.cursor.dirty = True

    def vpa(self, row):
        if row >= self.scroll_bottom:
            self.cursor.row = self.scroll_bottom - 1
        elif row < self.scroll_top:
            self.cursor.row = self.scroll_top
        else:
            self.cursor.row = row
        self.cursor.dirty = True

    def hvp(self, row, col):
        if row >= self.scroll_bottom:
            self.cursor.row = self.scroll_bottom - 1
        elif row < self.scroll_top:
            self.cursor.row = self.scroll_top
        else:
            self.cursor.row = row
        self.cursor.col = col
        self.cursor.dirty = True

    def cup(self, row, col):
        cursor = self.cursor
        if self.decom:
            top = self.scroll_top
            bottom = self.scroll_bottom
            row += top
            if row >= bottom:
                cursor.row = bottom - 1
            else:
                cursor.row = row
        else:
            bottom = self.height
            if row >= bottom:
                cursor.row = bottom - 1
            else:
                cursor.row = row
        cursor.col = col
        cursor.dirty = True

    def ed(self, ps):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        if ps == 0:
            line = self.lines[cursor.row]
            line.dirty = True
            attr = cursor.attr
            bcevalue = attr.getbcevalue()
            for cell in line.cells[cursor.col:]:
                cell.clear(bcevalue)
            if cursor.row < self.height:
                for line in self.lines[cursor.row + 1:]:
                    line.clear(bcevalue)
        elif ps == 1:
            line = self.lines[cursor.row]
            line.dirty = True
            bcevalue = cursor.attr.getbcevalue()
            for cell in line.cells[:cursor.col]:
                cell.clear(bcevalue)
            if cursor.row > 0:
                for line in self.lines[:cursor.row]:
                    line.clear(bcevalue)
        elif ps == 2:
            bcevalue = cursor.attr.getbcevalue()
            for line in self.lines:
                line.clear(bcevalue)

    def decaln(self):
        attr = self.cursor.attr
        for line in self.lines:
            line.dirty = True
            for cell in line.cells:
                cell.write(0x45, attr)  # E
        self.scroll_top = 0
        self.scroll_bottom = self.height

    def ris(self):
        cursor = self.cursor
        defaultvalue = cursor.attr.getdefaultvalue()
        for line in self.lines:
            line.clear(defaultvalue)
        self.dectcem = True
        cursor.clear()
        self._setup_tab()

    def reset_sgr(self):
        self.cursor.attr.clear()

    def sgr(self, pm):
        self.cursor.attr.set_sgr(pm)

    def ich(self, ps):
        ''' insert blank character(s) '''
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        row = cursor.row
        col = cursor.col
        if row >= self.scroll_bottom:
            self.cursor.row = self.scroll_bottom - 1
        elif row < self.scroll_top:
            self.cursor.row = self.scroll_top
        if col >= self.width:
            self.cursor.col = self.width - 1
        cells = self.lines[row].cells

        if col > 0 and cells[col - 1].get() == '\x00':
            col -= 1

        bcevalue = cursor.attr.getbcevalue()
        for i in xrange(0, ps):
            cell = cells.pop()
            cell.clear(bcevalue)
            cells.insert(col, cell)

    def cuu(self, ps):
        ''' cursor up '''
        if self.cursor.row >= self.scroll_top + ps:
            self.cursor.row -= ps
        else:
            self.cursor.row = self.scroll_top

    def cud(self, ps):
        if self.cursor.row < self.scroll_bottom - ps:
            self.cursor.row += ps
        else:
            self.cursor.row = self.scroll_bottom - 1

    def cuf(self, ps):
        if self.cursor.col < self.width - ps:
            self.cursor.col += ps
        else:
            self.cursor.col = self.width - 1

    def cub(self, ps):
        if self.cursor.col >= ps:
            self.cursor.col -= ps
        else:
            self.cursor.col = 0

    def dl(self, ps):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        row = self.cursor.row
        lines = self.lines
        bottom = self.scroll_bottom
        for line in lines[row + ps:bottom]:
            line.dirty = True
        for x in xrange(0, ps):
            lines.insert(bottom, Line(self.width))
            lines.pop(row)

    def il(self, ps):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        row = self.cursor.row
        lines = self.lines
        bottom = self.scroll_bottom
        for line in lines[row:bottom - ps]:
            line.dirty = True
        for x in xrange(0, ps):
            lines.pop(bottom - 1)
            lines.insert(row, Line(self.width))

    def el(self, ps):
        cursor = self.cursor
        if cursor.row >= self.height:
            cursor.row = self.height - 1
        if cursor.col >= self.width:
            cursor.col = self.width - 1
        line = self.lines[cursor.row]
        if ps == 0:
            cells = line.cells[cursor.col:]
        elif ps == 1:
            cells = line.cells[:cursor.col]
        elif ps == 2:
            cells = line.cells
        else:
            return
        line.dirty = True
        bcevalue = self.cursor.attr.getbcevalue()
        for cell in cells:
            cell.clear(bcevalue)


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
