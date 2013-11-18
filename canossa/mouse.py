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
import time

from constant import *

_DOUBLE_CLICK_SPAN = 0.2

class IMouseMode():

    def setenabled(self, value):
        raise NotImplementedError("IMouseMode::setenabled")

    def getprotocol(self):
        raise NotImplementedError("IMouseMode::getprotocol")

    def setprotocol(self, protocol):
        raise NotImplementedError("IMouseMode::setprotocol")

    def getencoding(self):
        raise NotImplementedError("IMouseMode::getencoding")

    def setencoding(self, encoding):
        raise NotImplementedError("IMouseMode::getencoding")

    def getfocusmode(self):
        raise NotImplementedError("IMouseMode::getfocusmode")

    def setfocusmode(self, mode):
        raise NotImplementedError("IMouseMode::setfocusmode")

class IFocusListener():

    def onfocusin(self):
        raise NotImplementedError("IFocusListener::onfocusin")

    def onfocusout(self):
        raise NotImplementedError("IFocusListener::onfocusout")


class IMouseListener():

    def mouseenabled(self):
        raise NotImplementedError("IMouseListener::mouseenabled")

    """ down/up """
    def onmousedown(self, context, x, y):
        raise NotImplementedError("IMouseListener::onmousedown")

    def onmouseup(self, context, x, y):
        raise NotImplementedError("IMouseListener::onmouseup")

    """ click/doubleclick """
    def onclick(self, context, x, y):
        raise NotImplementedError("IMouseListener::onclick")

    def ondoubleclick(self, context, x, y):
        raise NotImplementedError("IMouseListener::ondoubleclick")

    """ hover """
    def onmousehover(self, context, x, y):
        raise NotImplementedError("IMouseListener::onmousehover")

    """ scroll """
    def onscrolldown(self, context, x, y):
        raise NotImplementedError("IMouseListener::onscrolldown")

    def onscrollup(self, context, x, y):
        raise NotImplementedError("IMouseListener::onscrollup")

    """ drag and drop """
    def ondragstart(self, s, x, y):
        raise NotImplementedError("IMouseListener::ondragstart")

    def ondragend(self, s, x, y):
        raise NotImplementedError("IMouseListener::ondragend")

    def ondragmove(self, context, x, y):
        raise NotImplementedError("IMouseListener::ondragmove")


class IMouseModeImpl(IMouseMode):
    """
    >>> import StringIO
    >>> s = StringIO.StringIO()
    >>> mouse_mode = IMouseModeImpl()
    >>> mouse_mode.setenabled(s, True)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    <ESC>[?1000h<ESC>[?1002h<ESC>[?1003h<ESC>[?1004h<ESC>[?1015h<ESC>[?1006h
    >>> s.truncate(0)
    >>> mouse_mode.setenabled(s, False)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    <ESC>[?1000l<ESC>[?1004l
    >>> s.truncate(0)
    """

    _protocol = 0
    _encoding = 0
    _focusmode = 0

    def setenabled(self, s, value):

        if value:
            s.write(u"\x1b[?1000h")
            s.write(u"\x1b[?1002h")
            s.write(u"\x1b[?1003h")
            s.write(u"\x1b[?1004h")
            s.write(u"\x1b[?1015h")
            s.write(u"\x1b[?1006h")
            #s.write(u"\x1b[?30s\x1b[?30l") # hide scroll bar (rxvt)
            #s.write(u"\x1b[?7766s\x1b[?7766l") # hide scroll bar (MinTTY)
        else:
            if self._protocol == 0:
                s.write(u"\x1b[?1000l")
            else:
                s.write(u"\x1b[?%dl" % self._protocol)
                if self._encoding != 0:
                    s.write(u"\x1b[?%dl" % self._encoding)
            if self._focusmode == 0:
                s.write(u"\x1b[?1004l")
            #s.write(u"\x1b[?30r") # restore scroll bar state (rxvt)
            #s.write(u"\x1b[?7766r") # restore scroll bar state (MinTTY)

    def getprotocol(self):
        return self._protocol

    def setprotocol(self, protocol):
        self._protocol = protocol

    def getencoding(self):
        return self._encoding

    def setencoding(self, encoding):
        self._encoding = encoding

    def getfocusmode(self):
        return self._focusmode

    def setfocusmode(self, mode):
        self._focusmode = mode

def _parse_params(params, minimum=0, offset=0, minarg=1):
    param = 0
    for c in params:
        if c < 0x3a:
            param = param * 10 + c - 0x30
        elif c < 0x3c:
            param += offset
            if minimum > param:
                yield minimum
            else:
                yield param
            minarg -= 1
            param = 0
    param += offset
    if minimum > param:
        yield minimum
    else:
        yield param
    minarg -= 1
    yield param
    if minarg > 0:
        yield minimum

class ModeHandler(tff.DefaultHandler, IMouseModeImpl):

    def __init__(self, listener, termprop):
        self._listener = listener
        self._termprop = termprop

    def handle_esc(self, context, intermediate, final):
        if final == 0x63 and not intermediate: # RIS
            self.setprotocol(0)
            self.setencoding(0)
            self.setfocusmode(0)
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self._handle_mode(context, parameter, intermediate, final):
            return True
        if final == 0x72 and parameter:
            if parameter[0] == 0x3c and not intermediate:
                """ TTIMERS: CSI < Ps r """
                self._listener.notifyimerestore()
                return False
        if final == 0x73 and parameter:
            if parameter[0] == 0x3c and not intermediate:
                """ TTIMESV: CSI < Ps s """
                self._listener.notifyimesave()
                return False
        if final == 0x74 and parameter:
            if parameter[0] == 0x3c and not intermediate:
                """ TTIMEST: CSI < Ps t """
                length = len(parameter)
                if parameter == 1:
                    self._listener.notifyimeoff()
                elif parameter == 1 or parameter[2] == 0x3b:
                    if parameter[1] == 0x30:
                        self._listener.notifyimeoff()
                    elif parameter[1] == 0x31:
                        self._listener.notifyimeon()
                return False
        return False

    def _handle_mode(self, context, parameter, intermediate, final):
        if len(parameter) >= 5:
            if parameter[0] == 0x3f and not intermediate:
                params = _parse_params(parameter[1:])
                if final == 0x68: # 'h'
                    modes = self._set_modes(params)
                    if modes:
                        context.puts("\x1b[?%sh" % ";".join(modes))
                    return True
                elif final == 0x6c: # 'l'
                    modes = self._reset_modes(params)
                    if modes:
                        context.puts("\x1b[?%sl" % ";".join(modes))
                    return True
        return False

    def _set_modes(self, params):
        modes = []
        for param in params:
            if param >= 100:
                if param == MOUSE_PROTOCOL_NORMAL:
                    self.setprotocol(MOUSE_PROTOCOL_NORMAL)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_HIGHLIGHT:
                    self.setprotocol(MOUSE_PROTOCOL_HIGHLIGHT)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_BUTTON_EVENT:
                    self.setprotocol(MOUSE_PROTOCOL_BUTTON_EVENT)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_ANY_EVENT:
                    self.setprotocol(MOUSE_PROTOCOL_ANY_EVENT)
                    modes.append(str(param))
                elif param == FOCUS_EVENT_TRACKING:
                    self.setfocusmode(FOCUS_EVENT_TRACKING)
                elif param == MOUSE_ENCODING_UTF8:
                    self.setencoding(MOUSE_ENCODING_UTF8)
                elif param == MOUSE_ENCODING_URXVT:
                    self.setencoding(MOUSE_ENCODING_URXVT)
                elif param == MOUSE_ENCODING_SGR:
                    self.setencoding(MOUSE_ENCODING_SGR)
                elif param == 8840:
                    self._termprop.set_amb_as_double()
                    modes.append(str(param))
                elif param == 8428:
                    self._termprop.set_amb_as_single()
                    modes.append(str(param))
                elif param == 8441:
                    self._listener.notifyimeon()
                elif param >= 8860 and param < 8870:
                    if not self._listener.notifyenabled(param):
                        modes.append(str(param))
                else:
                    modes.append(str(param))
            else:
                modes.append(str(param))
        return modes

    def _reset_modes(self, params):
        modes = []
        for param in params:
            if param >= 1000:
                if param == MOUSE_PROTOCOL_NORMAL:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_HIGHLIGHT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_BUTTON_EVENT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == MOUSE_PROTOCOL_ANY_EVENT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == FOCUS_EVENT_TRACKING:
                    self.setfocusmode(0)
                elif param == MOUSE_ENCODING_UTF8:
                    self.setencoding(0)
                elif param == MOUSE_ENCODING_URXVT:
                    self.setencoding(0)
                elif param == MOUSE_ENCODING_SGR:
                    self.setencoding(0)
                elif param == 8840:
                    self._termprop.set_amb_as_single()
                    modes.append(str(param))
                elif param == 8428:
                    self._termprop.set_amb_as_double()
                    modes.append(str(param))
                elif param == 8441:
                    self._listener.notifyimeoff()
                elif param >= 8860 and param < 8870:
                    if not self._listener.notifydisabled(param):
                        modes.append(str(param))
                else:
                    modes.append(str(param))
            else:
                modes.append(str(param))
        return modes


class MouseDecoder(tff.DefaultHandler):

    always_handle = True

    def __init__(self, listener, termprop, mousemode):
        self._mouse_state = None
        self._x = -1
        self._y = -1
        self._lastclick = 0
        self._mousedown = False
        self._mousedrag = False
        self._init_glich_time = None
        self._mouse_mode = mousemode
        self._termprop = termprop
        self._listener = listener

    """ tff.EventObserver overrides """
    def handle_csi(self, context, parameter, intermediate, final):
        ''' '''
        if self._mouse_mode:
            try:
                mouse_info = self._decode_mouse(context, parameter, intermediate, final)
                if mouse_info:
                    if self._init_glich_time:
                        if time.time() - self._init_glich_time < 0.5:
                            self._init_glich_time = None
                            return False
                        self._init_glich_time = None
                    mode, mouseup, code, x, y = mouse_info
                    if mode == MOUSE_PROTOCOL_NORMAL:
                        self._mouse_state = []
                        return True
                    elif self.always_handle or self._listener.mouseenabled():
                        if mouseup:
                            code |= 0x3
                        self._dispatch_mouse(context, code, x, y)
                        return True
                    if self._mouse_mode.getprotocol() == MOUSE_ENCODING_SGR:
                        if mode == MOUSE_ENCODING_SGR:
                            return False
                        elif mode == MOUSE_ENCODING_URXVT:
                            params = (code + 32, x, y)
                            context.puts("\x1b[%d;%d;%dM" % params)
                            return True
                        elif mode == MOUSE_PROTOCOL_NORMAL:
                            params = (min(0x7e, code) + 32, x + 32, y + 32)
                            context.puts("\x1b[M%c%c%c" % params)
                            return True
                        return True
                    if self._mouse_mode.getprotocol() == MOUSE_ENCODING_URXVT:
                        if mode == MOUSE_ENCODING_URXVT:
                            return False
                        elif mode == MOUSE_ENCODING_SGR:
                            params = (code + 32, x, y)
                            if mouseup:
                                context.puts("\x1b[%d;%d;%dm" % params)
                            else:
                                context.puts("\x1b[%d;%d;%dM" % params)
                            return True
                        elif mode == MOUSE_PROTOCOL_NORMAL:
                            params = (min(0x7e, code) + 32, x + 32, y + 32)
                            context.puts("\x1b[M%c%c%c" % params)
                            return True
                    else:
                        return True
            finally:
                # TODO: logging
                pass

        if not intermediate:
            if not parameter:
                if final == 0x49: # I
                    self._listener.onfocusin()
                    return True
                elif final == 0x4f: # O
                    self._listener.onfocusout()
                    return True
        return False

    def initialize_mouse(self, output):
        self._mouse_mode.setenabled(output, True)
        self._x = -1
        self._y = -1
        self._init_glich_flag = time.time()

    def uninitialize_mouse(self, output):
        self._mouse_mode.setenabled(output, False)
        self._init_glich_flag = None

    def handle_char(self, context, c):
        # xterm's X10/normal mouse encoding could not be handled
        # by TFF filter because it is not ECMA-48 compatible sequense,
        # so we make custome handler and check 3 bytes after CSI M.
        if not self._mouse_state is None:
            if c >= 0x20 and c < 0x7f:
                self._mouse_state.append(c - 0x20)
                if len(self._mouse_state) == 3:
                    code, x, y = self._mouse_state
                    self._mouse_state = None
                    if self.always_handle or self._listener.mouseenabled():
                        self._dispatch_mouse(context, code, x - 1, y - 1)
                    if self._mouse_mode.getprotocol() != 0:
                        params = (code + 0x20, x + 0x20, y + 0x20)
                        context.puts("\x1b[M%c%c%c" % params)
                return True
        return False

    def _decode_mouse(self, context, parameter, intermediate, final):
        if not parameter:
            if final == 0x4d: # M
                return MOUSE_PROTOCOL_NORMAL, None, None, None, None
            return None
        elif parameter[0] == 0x3c:
            if final == 0x4d: # M
                p = ''.join([chr(c) for c in parameter[1:]])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    x -= 1
                    y -= 1
                except ValueError:
                    return False
                return MOUSE_ENCODING_SGR, False, code, x, y
            elif final == 0x6d: # m
                p = ''.join([chr(c) for c in parameter[1:]])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    x -= 1
                    y -= 1
                except ValueError:
                    return None
                return MOUSE_ENCODING_SGR, True, code, x, y
        elif 0x30 <= parameter[0] and parameter[0] <= 0x39:
            if final == 0x4d: # M
                p = ''.join([chr(c) for c in parameter])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    code -= 32
                    x -= 1
                    y -= 1
                except ValueError:
                    return False
                return 1015, False, code, x, y
        return None

    def _dispatch_mouse(self, context, code, x, y):
        if code & 32: # mouse move
            if x != self._x or y != self._y:
                if self._mousedrag:
                    self._listener.ondragmove(context, x, y)
                elif self._mousedown:
                    self._mousedrag = True
                    self._listener.ondragstart(context, x, y)
                else:
                    self._listener.onmousehover(context, x, y)
            self._x = x
            self._y = y

        elif code & 0x3 == 0x3: # mouse up
            if self._mousedown:
                self._mousedown = False
                if self._mousedrag:
                    self._mousedrag = False
                    self._listener.ondragend(context, x, y)
                elif x == self._x and y == self._y:
                    now = time.time()
                    if now - self._lastclick < _DOUBLE_CLICK_SPAN:
                        self._listener.ondoubleclick(context, x, y)
                    else:
                        self._listener.onclick(context, x, y)
                    self._lastclick = now
                self._listener.onmouseup(context, x, y)
            else:
                if x != self._x or y != self._y:
                    self._listener.onmousehover(context, x, y)
                self._x = x
                self._y = y

        elif code & 64: # mouse scroll
            if code & 0x1:
                self._listener.onscrollup(context, x, y)
            else:
                self._listener.onscrolldown(context, x, y)
        else: # mouse down
            self._x = x
            self._y = y
            self._listener.onmousedown(context, x, y)
            self._mousedown = True
            self._mousedrag = False

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

