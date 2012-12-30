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

def _param_generator(params, minimum=0, offset=0, minarg=1):
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
    if minarg > 0:
        yield minimum

def _parse_params(params, minimum=0, offset=0, minarg=1):
   return [param for param in _param_generator(params, minimum, offset, minarg)]

def _get_pos_and_size(stdin, stdout):
    import sys, os, termios, select
    
    stdin_fileno = stdin.fileno()
    vdisable = os.fpathconf(stdin_fileno, 'PC_VDISABLE')
    backup = termios.tcgetattr(stdin_fileno)
    new = termios.tcgetattr(stdin_fileno)
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(stdin_fileno, termios.TCSANOW, new)
    try:
        stdout.write("\x1b[6n")
        stdout.flush()
        
        rfd, wfd, xfd = select.select([stdin_fileno], [], [], 2)
        if rfd:
            data = os.read(stdin_fileno, 32)
            assert data[:2] == '\x1b['
            assert data[-1] == 'R'
            y, x = [int(n) - 1 for n in  data[2:-1].split(';')]

            stdout.write("\x1b[9999;9999H")
            try:
                stdout.write("\x1b[6n")
                stdout.flush()
                rfd, wfd, xfd = select.select([stdin_fileno], [], [], 2)
                stdout.flush()
                if rfd:
                    data = os.read(stdin_fileno, 32)
                    assert data[:2] == '\x1b['
                    assert data[-1] == 'R'
                    row, col = [int(n) for n in  data[2:-1].split(';')]
                    return (row, col, y, x)
            finally:
                stdout.write("\x1b[%d;%dH" % (y, x))
    finally:
        termios.tcsetattr(stdin_fileno, termios.TCSANOW, backup)

    
_CPR_NONE=0
_CPR_ANSI=1
_CPR_DEC=2

class Canossa(tff.DefaultHandler):

    __cpr = False

    def __init__(self,
                 scr=None,
                 termenc="UTF-8",
                 termprop=None,
                 visibility=False):

        self.__super = super(Canossa, self)

        if scr:
            self.screen = scr
        else:
            import sys, screen
            # make screen
            # get current position
            row, col, y, x = _get_pos_and_size(sys.stdin, sys.stdout)
            self.screen = screen.Screen(row, col, y, x, termenc, termprop)

        self.__visibility = visibility
        self.__cpr = False

    def handle_csi(self, context, parameter, intermediate, final):
        try:
            if len(intermediate) == 0:
                if final == 0x6d: # m
                    ''' SGR - Select Graphics Rendition '''
                    if len(parameter) == 0:
                        self.screen.reset_sgr()
                    else:
                        params = _param_generator(parameter)
                        self.screen.sgr(params)

                elif final == 0x48: # H
                    ''' CUP - Cursor Position '''
                    row, col = _param_generator(parameter, offset=-1, minarg=2)
                    self.screen.cup(row, col)

                elif final == 0x68: # h
                    if len(parameter) > 0:
                        if parameter[0] == 0x3f: #
                            params = _param_generator(parameter)
                            self.screen.decset(params)
                    return not self.__visibility

                elif final == 0x6c: # l
                    if len(parameter) > 0:
                        if parameter[0] == 0x3f: # ?
                            params = _param_generator(parameter)
                            self.screen.decrst(params)
                    return not self.__visibility

                elif final == 0x4b: # K
                    ''' EL - Erase Line(s) '''
                    ps = _parse_params(parameter)[0]
                    self.screen.el(ps)

                elif final == 0x4a: # J
                    ''' ED - Erase Display '''
                    ps = _parse_params(parameter)[0]
                    self.screen.ed(ps)

                elif final == 0x40: # @
                    ''' ICH - Insert Blank Character(s) '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.ich(ps)

                elif final == 0x41: # A
                    ''' CUU - Cursor Up '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.cuu(ps)

                elif final == 0x42: # B
                    ''' CUD - Cursor Down '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.cud(ps)

                elif final == 0x43: # C
                    ''' CUF - Cursor Forward '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.cuf(ps)

                elif final == 0x44: # D
                    ''' CUF - Cursor Backward '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.cub(ps)

                elif final == 0x4c: # L
                    ''' IL - Insert Line(s) '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.il(ps)

                elif final == 0x4d: # M
                    ''' DL - Down Line(s) '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.dl(ps)

                elif final == 0x50: # P
                    ''' DCH - Delete Char(s) '''
                    ps = _parse_params(parameter, minimum=1)[0]
                    self.screen.dch(ps)

                elif final == 0x63: # c DA2
                    ''' DA2 - Secondary Device Attribute '''
                    return not self.__visibility

                elif final == 0x64: # d
                    ''' VPA - Vertical Position Absolute '''
                    ps = _parse_params(parameter, offset=-1)[0]
                    self.screen.vpa(ps)

                elif final == 0x66: # f
                    ''' HVP - Horizontal and Vertical Position '''
                    row, col = _parse_params(parameter, offset=-1, minarg=2)
                    self.screen.hvp(row, col)

                elif final == 0x67: # g
                    ''' TBC - Tabstop Clear '''
                    ps = _parse_params(parameter)[0]
                    self.screen.tbc(ps)

                elif final == 0x6e: # n
                    ''' DSR - Device Status Request '''
                    if self.__visibility:
                        if parameter == [0x36]: # n
                            if intermediate == []: 
                                if not self._is_frame:
                                    self.__cpr = _CPR_ANSI
                                return True
                            elif intermediate == [0x3f]: # ?
                                if not self._is_frame:
                                    self.__cpr = _CPR_DEC
                                return True
                    return not self.__visibility

                elif final == 0x70: # p

                    if intermediate == []: 
                        if len(parameter) and parameter[0] == 0x3e: # >h
                            ''' DECRQM - Request DEC Private Mode '''
                    elif intermediate == [0x22]: # "
                        ''' DECSCL - Set Conformance Level '''
                        return not self.__visibility
                    elif intermediate == [0x24]: # $
                        if len(parameter) and parameter[0] == 0x3f: # ?
                            ''' DECRQM - Request DEC Private Mode '''
                            return not self.__visibility
                        else:
                            ''' DECRQM - Request ANSI Mode '''
                            return not self.__visibility
                    elif intermediate == [0x21]: # !
                        ''' DECTSR - Soft Reset '''
                        # TODO: implement soft reset
                        return not self.__visibility

                elif final == 0x72: # r
                    if len(parameter) > 0:
                        if parameter[0] == 0x3f: # ?
                            params = _parse_params(parameter[1:])
                            self.screen.xt_rest(params)
                        else:
                            top, bottom = _parse_params(parameter, offset=-1, minarg=2)
                            self.screen.decstbm(top, bottom)
                    else:
                        top, bottom = 0, self.screen.height - 1
                        self.screen.decstbm(top, bottom)

                elif final == 0x73: # s
                    if len(parameter) > 0:
                        if parameter[0] == 0x3f: # ?
                            params = _parse_params(parameter[1:])
                            self.screen.xt_save(params)

                elif final == 0x78: # x
                    return not self.__visibility

                #else:
                #    pass
                #    #mnemonic = '[' + chr(final) + ']'
                #    #raise Exception(mnemonic)
            #else:
            #    pass
            #    #mnemonic = '[' + str(intermediate) + ':' + chr(final) + ']'
            #    #raise Exception(mnemonic)
        #except ValueError:
        #    pass
        #except TypeError:
        #    pass
        finally:
            pass
        return True 

    def handle_esc(self, context, intermediate, final):
        if len(intermediate) == 0:
            if False:
                pass

            elif final == 0x37: # 7
                self.screen.cursor.save()
                return True
            elif final == 0x38: # 8
                self.screen.cursor.restore()
                return True
            elif final == 0x44: # D
                self.screen.ind()
            elif final == 0x45: # E
                self.screen.nel()
            elif final == 0x48: # H
                self.screen.hts()
            elif final == 0x4d: # M
                self.screen.ri()
            elif final == 0x63: # c
                self.screen.ris()
                return not self.__visibility # pass through
        elif intermediate == [0x23]: # #
            if final == 0x33: # 3
                self.screen.decdhlt()
            elif final == 0x34: # 4
                self.screen.decdhlb()
            elif final == 0x35: # 5
                self.screen.decswl()
            elif final == 0x36: # 6
                self.screen.decdwl()
            elif final == 0x38: # 8
                self.screen.decaln()
            else:
                pass
        elif intermediate == [0x28]: # (
            self.screen.set_g0(final)
            return True 
        elif intermediate == [0x29]: # )
            self.screen.set_g1(final)
            return True 
        else:
            return True 
        return True

    def handle_char(self, context, c):
        screen = self.screen
        if c <= 0x20:
            if c == 0x20: # SP
                screen.sp()
            elif c == 0x0a: # NL
                screen.lf()
            elif c == 0x0d: # CR
                screen.cr()
            elif c == 0x09: # HT
                screen.ht()
            elif c == 0x08: # BS
                screen.bs()
            elif c == 0x00: #NUL
                pass
            elif c == 0x05: # ENQ
                screen.write(c)
                return not self.__visibility
            elif c == 0x07: # BEL
                screen.write(c)
            elif c == 0x0b: # VT
                screen.lf()
            elif c == 0x0c: # FF
                screen.lf()
            elif c == 0x0e: # SO
                screen.so()
                return True 
            elif c == 0x0f: # SI
                screen.si()
                return True 
            else:
                pass
        else:
            screen.write(c)

        return True 

    def handle_draw(self, context):
        if self.__visibility:
            self.screen.drawall(context)
        if self.__cpr != _CPR_NONE:
            if self.__cpr == _CPR_ANSI:
                self.__cpr = _CPR_NONE
                context.puts("\x1b[6n")
            elif self.__cpr == _CPR_DEC:
                self.__cpr = _CPR_NONE
                context.puts("\x1b[?6n")

    def handle_resize(self, context, row, col):
        try:
            self.screen.resize(row, col)
        except:
            pass



