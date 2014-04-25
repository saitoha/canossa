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
import logging

from interface import IModeListener
from interface import IListbox, IListboxListener
from mouse import IFocusListener, IMouseListener

_POPUP_DIR_NORMAL = True
_POPUP_DIR_REVERSE = False
#_POPUP_WIDTH_MAX = 20
_POPUP_HEIGHT_MAX = 12


class IModeListenerImpl(IModeListener):

    _has_event = False
    _imemode = True
    _savedimemode = True

    def notifyenabled(self, n):
        if n == 8861:
            self._has_event = True
        elif n == 8860:
            self._imemode = True

    def notifydisabled(self, n):
        if n == 8861:
            self._has_event = False
        elif n == 8860:
            self.reset()
            self._imemode = False

    def notifyimeon(self):
        self._imemode = True

    def notifyimeoff(self):
        self.reset()
        self._imemode = False

    def notifyimesave(self):
        self._savedimemode = self._imemode

    def notifyimerestore(self):
        self._imemode = self._savedimemode

    def reset(self):
        pass

    def hasevent(self):
        return self._has_event

    def getenabled(self):
        return self._imemode


class IListboxImpl(IListbox):

    _style_active = {'selected': u'\x1b[0;1;37;42m',
                     'unselected': u'\x1b[0;1;37;41m',
                     'scrollbar': u'\x1b[0;47m',
                     'slider': u'\x1b[0;44m'}

    _style_scrollbar_hover = {'selected': u'\x1b[0;1;37;42m',
                              'unselected': u'\x1b[0;1;37;41m',
                              'scrollbar': u'\x1b[0;47m',
                              'slider': u'\x1b[0;45m'}

    _style_scrollbar_drag = {'selected': u'\x1b[0;1;37;42m',
                             'unselected': u'\x1b[0;1;37;41m',
                             'scrollbar': u'\x1b[0;47m',
                             'slider': u'\x1b[0;46m'}

    _style_inactive = {'selected': u'\x1b[0;1;37;41m',
                       'unselected': u'\x1b[0;1;37;42m',
                       'scrollbar': u'',
                       'slider': u''}

    _style = _style_active

    innerscreen = None
    _dirty = True

    """ IListbox implementation """
    def assign(self, l, index=0):
        y, x = self._screen.getyx()
        self.setposition(x, y)
        self._list = l
        self._index = index
        self.notifyselection()
        self.focus()
        self._dirty = True

    def isempty(self):
        return self._list is None

    def reset(self):
        self._width = 8
        self._height = 0
        self._left = 0
        self._top = 0
        self._offset_left = 0
        self._offset_top = 0
        self._list = None
        self._index = 0
        self._scrollpos = 0
        self._dirty = True

    def notifyselection(self):
        if self._index == -1:
            return
        value = self._list[self._index]

        pos = value.find(u';')
        if pos >= 0:
            text = value[:pos]
            remarks = value[pos:]
        else:
            text = value
            remarks = None

        self._listener.onselected(self, self._index, text, remarks)

    def movenext(self):
        if self._list and self._index < len(self._list) - 1:
            self._index += 1
            if self._index - self._height + 1 > self._scrollpos:
                self._listener.onrepeat(self)
                self._scrollpos = self._index - self._height + 1
            self.notifyselection()
            self._dirty = True
            return True
        return False

    def moveprev(self):
        if self._list and self._index > 0:
            self._index -= 1
            if self._index < self._scrollpos:
                self._scrollpos = self._index
            self.notifyselection()
            self._dirty = True
            return True
        return False

    def jumpnext(self):
        for i in xrange(0, self._height):
            if self._index >= len(self._list):
                return False
            self._dirty = True
            self.movenext()
        return True

    def _calculate_scrollbar_postion(self):
        height = self._height
        scroll_pos = self._scrollpos
        all_length = len(self._list)
        if height < all_length:
            start_pos = round(1.0 * scroll_pos / all_length * height)
            end_pos = start_pos + round(1.0 * height / all_length * height + 1)
            if start_pos > height - 1:
                start_pos = height - 1
                end_pos = height
            return start_pos, end_pos
        return None

    def moveto(self, row, col):
        screen = self._screen
        if col >= screen.width + 1:
            raise Exception("range error col=%s" % col)
        if row >= screen.height + 1:
            raise Exception("range error row=%s" % row)
        if row < 1:
            raise Exception("range error row=%s" % row)
        if col < 1:
            raise Exception("range error col=%s" % col)
        self._window.write('\x1b[%d;%dH' % (row, col))

    # IWidget
    def setdirty(self):
        pass

    def focus(self):
        self._window.focus()
        self._dirty = True

    def blur(self):
        self._window.blur()

    def getlabel(self):
        return None 

    def checkdirty(self, region):
        if self._dirty:
            region.sub(self._left + self._offset_left, self._top + self._offset_top, self._width, self._height)
            self._dirty = False

    def drawcursor(self):
        pass

    def draw(self, region):
        window = self._window
        if self._list:
            display = self._getdisplayinfo()
            left = display.left
            top = display.top
            width = display.width
            height = display.height

            self._left = left
            self._top = top
            self._width = width
            self._height = height

            left += self._offset_left
            top += self._offset_top

            if window.is_shown():
                window.realloc(left, top, width, height)
            else:
                window.alloc(left, top, width, height)
                self._style = self._style_active
                self._mouse_decoder.initialize_mouse(window)

            dirtyregion = region.add(left, top, width, height)

            style_selected = self._style['selected']
            style_unselected = self._style['unselected']
            style_scrollbar = self._style['scrollbar']
            style_slider = self._style['slider']

            scrollbar_info = self._calculate_scrollbar_postion()
            if scrollbar_info:
                start_pos, end_pos = scrollbar_info

            screen = self._screen
            for i, value in enumerate(display.candidates):
                if top + i < 0:
                    continue
                if top + i >= screen.height:
                    break

                dirtyrange = dirtyregion[top + i]

                if dirtyrange:

                    dirty_left = min(dirtyrange)
                    if dirty_left < 0:
                        dirty_left = 0

                    dirty_right = max(dirtyrange) + 1
                    if dirty_right > screen.width:
                        dirty_right = screen.width

                    if dirty_left > dirty_right:
                        continue

#                    dirtyrange.difference_update(xrange(left, left + width))

                    self.moveto(top + 1 + i, dirty_left + 1)

                    if i == display.pos: # selected line
                        window.write(style_selected)
                    else: # unselected lines
                        window.write(style_unselected)

                    wcwidth = self._termprop.wcwidth
                    n = left

                    for c in value:
                        length = wcwidth(ord(c))
                        if n + length > dirty_right:
                            break
                        if n >= dirty_left:
                            window.write(c)
                        n += length
                        if length == 2 and n == dirty_left + 1:
                            window.write(u' ')
                            n += 1

                    while True:
                        if n >= dirty_right:
                            break
                        if n >= left + width - 1:
                            if scrollbar_info:
                                if i >= start_pos and i < end_pos:
                                    window.write(style_slider)
                                else:
                                    window.write(style_scrollbar)
                            window.write(u' ')
                            break
                        n += 1
                        if n < dirty_left + 1:
                            continue
                        window.write(u' ')
            screen.cursor.attr.draw(window)

            return True
        return False

    def close(self):
        if self.isshown():
            window = self._window
            window.dealloc()

            if not self._mousemode is None:
                if not self._screen.has_visible_windows():
                    self._mouse_decoder.uninitialize_mouse(window)
        self.reset()

    def isshown(self):
        return self._window.is_shown()

    def _truncate_str(self, s, length):
        wcwidth = self._termprop.wcwidth
        l = 0
        for i in xrange(0, len(s)):
            if l > length:
                return s[:i] + u"..."
            c = s[i]
            l += wcwidth(ord(c))
        return s

    def setposition(self, x, y):
        self._x = x
        self._y = y

    def is_moved(self):
        if self._offset_left == 0:
            return True
        if self._offset_top == 0:
            return True
        return False

    def _getdisplayinfo(self):
        width = 0
        candidates = self._list

        x = self._x
        y = self._y

        vdirection = self._getdirection(y)
        if vdirection == _POPUP_DIR_NORMAL:
            height = self._screen.height - (y + 1)
        else:
            height = y

        height = min(height, _POPUP_HEIGHT_MAX)

        candidates_length = len(candidates)
        if candidates_length > height:
            candidates = candidates[self._scrollpos:self._scrollpos + height]
            pos = self._index - self._scrollpos
        else:
            pos = self._index

        for value in candidates:
            length = self._termprop.wcswidth(value)
            width = max(width, length)

        candidates = [self._truncate_str(s, width) for s in candidates]
        width += 4

        height = min(height, candidates_length)

        if x + width > self._screen.width:
            offset = x + width - self._screen.width + 1
        else:
            offset = 0

        if vdirection == _POPUP_DIR_NORMAL:
            top = y + 1
        else:
            top = y - height

        if offset > 0:
            left = x - offset
        else:
            left = x

        return DisplayInfo(candidates, pos, left, top, width, height)

    def _getdirection(self, row):
        screen = self._screen
        if row * 2 > screen.height:
            return _POPUP_DIR_REVERSE
        return _POPUP_DIR_NORMAL


class IFocusListenerImpl(IFocusListener):

    def __init__(self):
        self._style = self._style_inactive

    """ IFocusListener implementation """
    def onfocusin(self):
        self._style = self._style_active

    def onfocusout(self):
        self._style = self._style_inactive
        if self.isshown():
            self.close()


_HITTEST_NONE = 0x0
_HITTEST_BODY_SELECTED = 0x1
_HITTEST_BODY_UNSELECTED = 0x2
_HITTEST_SLIDER_INNER = 0x3
_HITTEST_SLIDER_ABOVE = 0x4
_HITTEST_SLIDER_BELOW = 0x5

_DRAGMODE_NONE = 0x0
_DRAGMODE_MOVE = 0x1
_DRAGMODE_SCROLL = 0x2


class IMouseListenerImpl(IMouseListener):

    def __init__(self):
        self._dragmode = _DRAGMODE_NONE
        self._scrollorigin = 0
        self._lasthittest = None

    """ IMouseListener implementation """
    def mouseenabled(self):
        return self.isshown()

    def onmousedown(self, context, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_NONE:
            return False
        self._lasthittest = hittest
        self.focus()
        self._style = self._style_scrollbar_drag
        return True

    def onmouseup(self, context, x, y):
        hittest = self._hittest(x, y)
        self._lasthittest = hittest
        if hittest == _HITTEST_NONE:
            return False
        #self._style = self._style_active
        self._screen.setfocus()
        return True

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_NONE:
            return False
        self._lasthittest = hittest
        if hittest == _HITTEST_BODY_SELECTED:
            self._listener.onsettled(self, context)
        elif hittest == _HITTEST_BODY_UNSELECTED:
            x -= self._offset_left
            y -= self._offset_top
            n = y - self._top
            while self._scrollpos + n < self._index:
                self.moveprev()
            while self._scrollpos + n > self._index:
                self.movenext()
        elif hittest == _HITTEST_SLIDER_ABOVE:
            for i in xrange(0, self._height):
                if self._index <= 0:
                    break
                self.moveprev()
        elif hittest == _HITTEST_SLIDER_INNER:
            pass
        elif hittest == _HITTEST_SLIDER_BELOW:
            for i in xrange(0, self._height):
                if self._index >= len(self._list):
                    break
                self.movenext()
        return True

    def ondoubleclick(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_BODY_SELECTED:
            self._listener.onsettled(self, context)
        elif hittest == _HITTEST_SLIDER_ABOVE:
            for i in self._list:
                if self._index <= 0:
                    break
                self.moveprev()
        elif hittest == _HITTEST_SLIDER_BELOW:
            for i in self._list:
                if self._index >= len(self._list):
                    break
                self.movenext()
        return True

    def onmousehover(self, context, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_BODY_UNSELECTED:
            x -= self._offset_left
            y -= self._offset_top
            n = y - self._top
            while self._scrollpos + n < self._index:
                self.moveprev()
            while self._scrollpos + n > self._index:
                self.movenext()
            self._style = self._style_active
        elif hittest == _HITTEST_SLIDER_INNER:
            self._style = self._style_scrollbar_hover
        else:
            self._style = self._style_active
        return True

    """ scroll """
    def onscrolldown(self, context, x, y):
        self.movenext()
        return True

    def onscrollup(self, context, x, y):
        self.moveprev()
        return True

    """ drag and drop """
    def ondragstart(self, s, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_NONE:
            return False
        elif hittest == _HITTEST_BODY_UNSELECTED or hittest == _HITTEST_BODY_SELECTED:
            self._dragmode = _DRAGMODE_MOVE
            x -= self._offset_left
            y -= self._offset_top
            self._dragpos = (x, y)
        else:
            self._dragmode = _DRAGMODE_SCROLL
            self._scrollorigin = self._scrollpos
            self._dragpos = (x, y)
        return True

    def ondragend(self, s, x, y):
        if self._dragmode == _DRAGMODE_NONE:
            return False
        self._dragpos = None
        self._dragmode = _DRAGMODE_NONE
        self._scrollorigin = 0
        return True

    def ondragmove(self, context, x, y):
        if not self._dragpos:
            return False
        self._dirty = True
        if self._dragmode == _DRAGMODE_MOVE:
            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._screen
            if self._left + self._width + offset_x < 1:
                offset_x = 1 - self._left - self._width
            elif self._left + offset_x > screen.width - 1:
                offset_x = screen.width - self._left - 1
            if self._top + self._height + offset_y < 1:
                offset_y = 1 - self._top - self._height
            elif self._top + offset_y > screen.height - 1:
                offset_y = screen.height - self._top - 1

            self._offset_left = offset_x
            self._offset_top = offset_y
            return True
        elif self._dragmode == _DRAGMODE_SCROLL:
            all_length = len(self._list)
            origin_x, origin_y = self._dragpos
            offset_y = (y - origin_y) * all_length / self._height
            #offset_y = y - origin_y
            self._scrollpos = self._scrollorigin + offset_y
            if self._scrollpos < 0:
                self._scrollpos = 0
            elif self._scrollpos > all_length - self._height - 1:
                self._scrollpos = all_length - self._height - 1
            if self._index != -1:
                if self._index < self._scrollpos:
                    self._index = self._scrollpos
                    self.notifyselection()
                elif self._index > self._scrollpos + self._height - 1:
                    self._index = self._scrollpos + self._height - 1
                    self.notifyselection()
            return True
        return False

    def _hittest(self, x, y):
        if not self.isshown():
            return _HITTEST_NONE

        x -= self._offset_left
        y -= self._offset_top

        if x < self._left:
            return _HITTEST_NONE
        if x >= self._left + self._width:
            return _HITTEST_NONE
        if y < self._top:
            return _HITTEST_NONE
        if y >= self._top + self._height:
            return _HITTEST_NONE
        if x == self._left + self._width - 1:
            scrollbar_info = self._calculate_scrollbar_postion()
            if not scrollbar_info is None:
                start, end = scrollbar_info
                if y - self._top < start:
                    return _HITTEST_SLIDER_ABOVE
                if y - self._top < end:
                    return _HITTEST_SLIDER_INNER
                return _HITTEST_SLIDER_BELOW
        if self._scrollpos + y - self._top == self._index:
            return _HITTEST_BODY_SELECTED
        return _HITTEST_BODY_UNSELECTED



class DisplayInfo():

    def __init__(self, candidates, pos, left, top, width, height):
        self.candidates = candidates
        self.pos = pos
        self.left = left
        self.top = top
        self.width = width
        self.height = height


class Listbox(tff.DefaultHandler,
              IListboxImpl,
              IFocusListenerImpl,
              IMouseListenerImpl):

    def __init__(self, listener, screen, termprop, mousemode, mouse_decoder):

        assert isinstance(listener, IListboxListener)

        IFocusListenerImpl.__init__(self)
        IMouseListenerImpl.__init__(self)

        self._mouse_decoder = mouse_decoder

        self._screen = screen
        self._listener = listener
        self._termprop = termprop
        self._mousemode = mousemode
        self._window = screen.create_window(self)
        self._left = 0
        self._top = 0
        self._width = 10
        self._height = _POPUP_HEIGHT_MAX
        self._offset_left = 0
        self._offset_top = 0
        self._dragpos = None
        self._list = None
        self._index = 0
        self._scrollpos = 0

    def set_offset(self, offset_x, offset_y):

        display = self._getdisplayinfo()

        screen = self._screen

        if display.left + offset_x < 0:
            offset_x = 0 - self._left
        elif display.left + display.width + offset_x > screen.width - 1:
            offset_x = screen.width - display.left - display.width

        self._offset_left = offset_x
        self._offset_top = offset_y

    """ tff.EventObserver override """
    def handle_char(self, context, c):
        if self.isshown():
            if self._listener.oninput(self, context, c):
                return True
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self.isshown():
            if self._handle_csi_cursor(context, parameter,
                                       intermediate, final):
                return True
        return False

    def handle_esc(self, context, intermediate, final):
        if self.isshown():
            if final == 0x76: # C-v
                if not intermediate:
                    for i in xrange(0, self._height):
                        if self._index <= 0:
                            break
                        self.moveprev()
                    return True
        return False

    def handle_ss3(self, context, final):
        if self.isshown():
            if self._handle_ss3_cursor(context, final):
                return True
        if final == 0x5b:  # [
            self._listener.oncancel(self, context)
            return False
        return False

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if not intermediate:
            if final == 0x41:  # A
                if not intermediate:
                    self.moveprev()
                    return True
            elif final == 0x42:  # B
                if not intermediate:
                    self.movenext()
                    return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if final == 0x41:  # A
            self.moveprev()
            return True
        elif final == 0x42:  # B
            self.movenext()
            return True
        return False


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
