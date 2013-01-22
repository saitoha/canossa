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
import logging

from interface import IModeListener, IListbox, IListboxListener
from mouse import IFocusListener, IMouseListener, MouseDecoder

_POPUP_DIR_NORMAL = True
_POPUP_DIR_REVERSE = False
_POPUP_WIDTH_MAX = 20
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

    _style_active          = { 'selected'  : u'\x1b[0;1;37;42m',
                               'unselected': u'\x1b[0;1;37;41m',
                               'scrollbar' : u'\x1b[0;47m',
                               'slider'    : u'\x1b[0;44m',
                             }

    _style_scrollbar_hover = { 'selected'  : u'\x1b[0;1;37;42m',
                               'unselected': u'\x1b[0;1;37;41m',
                               'scrollbar' : u'\x1b[0;47m',
                               'slider'    : u'\x1b[0;45m',
                             }

    _style_scrollbar_drag  = { 'selected'  : u'\x1b[0;1;37;42m',
                               'unselected': u'\x1b[0;1;37;41m',
                               'scrollbar' : u'\x1b[0;47m',
                               'slider'    : u'\x1b[0;46m',
                             }

    _style_inactive        = { 'selected'  : u'\x1b[0;1;37;41m',
                               'unselected': u'\x1b[0;1;37;42m',
                               'scrollbar' : u'',
                               'slider'    : u'',
                             }

    _style = _style_active
    _show = False

    """ IListbox implementation """
    def assign(self, l, index=0):
        self._list = l
        self._index = index
        self.notifyselection()

    def isempty(self):
        return self._list == None

    def reset(self):
        self._width = 8
        self._height = 0
        self._left = None
        self._top = None
        self._offset_left = 0
        self._offset_top = 0
        self._list = None
        self._index = 0
        self._scrollpos = 0

    def notifyselection(self):
        value = self._list[self._index]

        pos = value.find(u";")
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
            return True
        return False

    def moveprev(self):
        if self._list and self._index > 0:
            self._index -= 1
            if self._index < self._scrollpos:
                self._scrollpos = self._index
            self.notifyselection()
            return True
        return False

    def jumpnext(self):
        for i in xrange(0, self._height):
            if self._index >= len(self._list):
                return False
            self.movenext()
        return True

    def _calculate_scrollbar_postion(self):
        height = self._height
        scroll_pos = self._scrollpos
        all_length = len(self._list)
        if height < all_length:
            start_pos = round(1.0 * scroll_pos / all_length * height)
            end_pos = start_pos + round(1.0 * height / all_length * height + 1.0)
            if start_pos > height - 1:
                start_pos = height - 1
                end_pos = height
            return start_pos, end_pos
        return None

    def draw(self, s):
        if self._list:
            l, pos, left, top, width, height = self._getdisplayinfo()
            if self._show:
                screen = self._screen
                if self._left < left:
                    screen.copyrect(s,
                                    self._left + self._offset_left,
                                    top + self._offset_top,
                                    left - self._left,
                                    self._height + self._top - top)
                if self._left + self._width > left + width:
                    screen.copyrect(s,
                                    left + width + self._offset_left,
                                    top + self._offset_top,
                                    self._left + self._width - (left + width),
                                    height)
                if self._top + self._height > top + height:
                    screen.copyrect(s,
                                    left + self._offset_left,
                                    top + height + self._offset_top,
                                    self._left + self._width,
                                    self._height - height)
                if self._top < top:
                    screen.copyrect(s,
                                    self._left + self._offset_left,
                                    self._top + self._offset_top,
                                    self._width,
                                    top - self._top)

            elif not self._mousemode is None:
                self._style = self._style_active
                self._mouse_decoder.initialize_mouse(self._output)
       
            self._left = left 
            self._top = top 
            self._width = width
            self._height = height

            left += self._offset_left
            top += self._offset_top

            style_selected = self._style['selected']
            style_unselected = self._style['unselected']
            style_scrollbar = self._style['scrollbar']
            style_slider = self._style['slider']

            scrollbar_info = self._calculate_scrollbar_postion()
            if scrollbar_info:
                start_pos, end_pos = scrollbar_info
            for i, value in enumerate(l):
                if i == pos: # selected line 
                    s.write(style_selected)
                else: # unselected lines 
                    s.write(style_unselected)
                s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
                s.write(u' ' * (width - 1))
                if scrollbar_info:
                    if i >= start_pos and i < end_pos:
                        s.write(style_slider)
                    else:
                        s.write(style_scrollbar)
                s.write(u' ')
                if i == pos: # selected line 
                    s.write(style_selected)
                else: # unselected lines 
                    s.write(style_unselected)
                if i == pos: s.write(u'\x1b[1m')
                s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
                s.write(value)
                s.write(u'\x1b[m')

            y, x = self._screen.getyx()
            s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
            self._show = True
            return True
        return False

    def close(self):
        if self.isshown(): 
            s = self._output
            y, x = self._screen.getyx()
            s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._show = False
            self._screen.copyrect(s,
                                  self._left + self._offset_left,
                                  self._top + self._offset_top,
                                  self._width,
                                  self._height)
            s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            if not self._mousemode is None:
                self._mouse_decoder.uninitialize_mouse(self._output)

        self.reset()
 
    def isshown(self):
        return self._show

    def _truncate_str(self, s, length):
        if self._termprop.wcswidth(s) > length:
            return s[:length] + u"..."
        return s

    def _getdisplayinfo(self):
        width = 0
        candidates = self._list

        y, x = self._screen.getyx()

        vdirection = self._getdirection(y)
        if vdirection == _POPUP_DIR_NORMAL:
            height = self._screen.height - (y + 1) 
        else:
            height = y 

        height = min(height, _POPUP_HEIGHT_MAX)

        if len(candidates) > height:
            candidates = candidates[self._scrollpos:self._scrollpos + height]
            pos = self._index - self._scrollpos
        else:
            pos = self._index

        for value in candidates:
            length = self._termprop.wcswidth(value)
            if length > _POPUP_WIDTH_MAX:
                length = self._termprop.wcswidth(value)
            width = max(width, length + 6)

        candidates = [self._truncate_str(s, width) for s in candidates]

        height = min(height, len(candidates))

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

        return candidates, pos, left, top, width, height

    def _getdirection(self, row):
        screen = self._screen
        if row * 2 > screen.height:
            vdirection = _POPUP_DIR_REVERSE
        else:            
            vdirection = _POPUP_DIR_NORMAL 
        return vdirection

class IFocusListenerImpl(IFocusListener):

    """ IFocusListener implementation """
    def onfocusin(self):
        self._style = self._style_active

    def onfocusout(self):
        self._style = self._style_inactive

_HITTEST_NONE            = 0x0
_HITTEST_BODY_SELECTED   = 0x1
_HITTEST_BODY_UNSELECTED = 0x2
_HITTEST_SLIDER_INNER    = 0x3
_HITTEST_SLIDER_ABOVE    = 0x4
_HITTEST_SLIDER_BELOW    = 0x5

_DRAGMODE_MOVE   = 0x0
_DRAGMODE_SCROLL = 0x1

class IMouseListenerImpl(IMouseListener):

    _dragmode = _DRAGMODE_MOVE
    _scrollorigin = 0
    _lasthittest = None 

    """ IMouseListener implementation """

    def mouseenabled(self):
        return self.isshown()

    def onmousedown(self, context, x, y):
        self._style = self._style_scrollbar_drag

    def onmouseup(self, context, x, y):
        self._style = self._style_active

    def onclick(self, context, x, y):
        hittest = self._hittest(x, y)
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
        elif self.isshown():
            self.close()

    def ondoubleclick(self, context, x, y):
        hittest = self._lasthittest
        if hittest == _HITTEST_BODY_SELECTED:
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

    def onmousehover(self, context, x, y):
        hittest = self._hittest(x, y)
        if self.isshown():
            if hittest == _HITTEST_BODY_UNSELECTED:
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

    """ scroll """
    def onscrolldown(self, context, x, y):
        self.movenext()

    def onscrollup(self, context, x, y):
        self.moveprev()

    """ drag and drop """
    def ondragstart(self, s, x, y):
        hittest = self._hittest(x, y)
        if hittest == _HITTEST_BODY_UNSELECTED or hittest == _HITTEST_BODY_SELECTED:
            self._dragmode = _DRAGMODE_MOVE
            x -= self._offset_left
            y -= self._offset_top
            self._dragpos = (x, y)
        #elif hittest == _HITTEST_SLIDER_INNER or hittest == _HITTEST_SLIDER_ABOVE or hittest == _HITTEST_SLIDER_BELOW:
        else:
            self._dragmode = _DRAGMODE_SCROLL
            self._scrollorigin = self._scrollpos
            self._dragpos = (x, y)

    def ondragend(self, s, x, y):
        self._dragpos = None
        self._dragmode = _DRAGMODE_MOVE
        self._scrollorigin = 0

    def ondragmove(self, context, x, y):
        if self._dragpos:
            if self._dragmode == _DRAGMODE_MOVE:
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

                s = self._output
                self._clearDeltaX(s, offset_x)
                self._clearDeltaY(s, offset_y)

                self._offset_left = offset_x
                self._offset_top = offset_y 
            elif self._dragmode == _DRAGMODE_SCROLL:
                all_length = len(self._list)
                origin_x, origin_y = self._dragpos
                offset_y = int(1.0 * (y - origin_y) / self._height * all_length)
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

    def _hittest(self, x, y):
        x -= self._offset_left
        y -= self._offset_top
        if not self.isshown():
            return _HITTEST_NONE
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

class Listbox(tff.DefaultHandler,
              IListboxImpl,
              IFocusListenerImpl,
              IMouseListenerImpl):

    _left = None
    _top = None
    _width = 10
    _height = _POPUP_HEIGHT_MAX
    _offset_left = 0
    _offset_top = 0

    _output = None

    _show = False 
    _mousemode = None
    _dragpos = None

    _list = None
    _index = 0
    _scrollpos = 0

    _listener = None

    def __init__(self, listener, screen, termprop, mousemode, output):
        self._mouse_decoder = MouseDecoder(self, termprop, mousemode)
        self._screen = screen
        self._listener = listener
        self._termprop = termprop
        self._mousemode = mousemode
        self._output = output

    def set_offset(self, offset_x, offset_y):

        l, pos, left, top, width, height = self._getdisplayinfo()

        screen = self._screen

        if left + offset_x < 0:
            offset_x = 0 - self._left
        elif left + width + offset_x > screen.width - 1:
            offset_x = screen.width - left - width

        self._offset_left = offset_x
        self._offset_top = offset_y

    """ tff.EventObserver override """
    def handle_char(self, context, c):
        if self.isshown():
            if self._mouse_decoder.handle_char(context, c):
                return True
            if self._listener.oninput(self, context, c):
                return True
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self.isshown():
            if self._handle_csi_cursor(context, parameter, intermediate, final):
                return True
            if self._mouse_decoder.handle_csi(context, parameter, intermediate, final):
                return True
        return False

    def handle_esc(self, context, intermediate, final):
        if self.isshown():
            if final == 0x76 and len(intermediate) == 0: # C-v
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
        if final == 0x5b: # [
            self._listener.oncancel(self, context)
            return False
        return False

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if len(intermediate) == 0:
            if final == 0x41: # A
                self.moveprev()
                return True
            elif final == 0x42: # B
                self.movenext()
                return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if final == 0x41: # A
            self.moveprev()
            return True
        elif final == 0x42: # B
            self.movenext()
            return True
        return False

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

