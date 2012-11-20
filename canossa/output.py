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
import threading

def _parse_params(params, minimum=0, offset=0, maxarg=255):
    def param_generator():
        for p in ''.join([chr(p) for p in params]).split(';')[:maxarg]:
            if p == '':
                yield minimum 
            else:
                yield max(minimum, int(p) + offset)
    return [param for param in param_generator()]

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

    
class OutputHandler(tff.DefaultHandler):

    def __init__(self, scr=None, visibility=False):
        self.__super = super(OutputHandler, self)

        if scr:
            self.__screen = scr
        else:
            import sys, screen
            # make screen
            # get current position
            row, col, y, x = _get_pos_and_size(sys.stdin, sys.stdout)
            self.__screen = screen.Screen(row, col, y, x)

        self.__super = super(OutputHandler, self)
        self.__visibility = visibility

    def handle_csi(self, context, parameter, intermediate, final):
        p = ''.join([chr(c) for c in parameter])
        i = ''.join([chr(c) for c in intermediate])
        f = chr(final)
        if i == '':
            if False:
                pass

            elif final == 0x41: # A
                mnemonic = 'CUU'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.cuu(ps)

            elif final == 0x42: # B
                mnemonic = 'CUD'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.cud(ps)

            elif final == 0x43: # C
                mnemonic = 'CUF'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.cuf(ps)

            elif final == 0x44: # D
                mnemonic = 'CUB'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.cub(ps)

            elif final == 0x48: # H
                mnemonic = 'CUP'
                if len(parameter) > 0:
                    row, col = _parse_params(parameter, offset=-1)
                else:
                    row, col = 0, 0
                self.__screen.cup(row, col)

            elif final == 0x4a: # J
                mnemonic = 'ED'
                if len(parameter) == 0:
                    ps = 0
                else:
                    ps = _parse_params(parameter)[0]
                self.__screen.ed(ps)

            elif final == 0x4b: # K
                mnemonic = 'EL'
                if len(parameter) == 0:
                    ps = 0
                else:
                    ps = _parse_params(parameter)[0]
                self.__screen.el(ps)

            elif final == 0x4c: # L
                mnemonic = 'IL'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.il(ps)

            elif final == 0x4d: # M
                mnemonic = 'DL'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.dl(ps)

            elif final == 0x50: # P
                mnemonic = 'DCH'
                if len(parameter) == 0:
                    ps = 1
                else:
                    ps = _parse_params(parameter, minimum=1)[0]
                self.__screen.dch(ps)

            elif final == 0x63: # c DA2
                return not self.__visibility

            elif final == 0x64: # d
                mnemonic = 'VPA'
                if len(parameter) > 0:
                    ps = _parse_params(parameter, offset=-1)[0]
                else:
                    ps = 0
                self.__screen.vpa(ps)

            elif final == 0x66: # f
                mnemonic = 'HVP'
                if len(parameter) > 0:
                    row, col = _parse_params(parameter, offset=-1)
                else:
                    row, col = 0, 0
                self.__screen.hvp(row, col)

            elif final == 0x67: # g
                mnemonic = 'TBC'
                if len(parameter) == 0:
                    ps = 0
                else:
                    params = _parse_params(parameter)
                    ps = params[0] 
                self.__screen.tbc(ps)

            elif final == 0x68: # h
                if len(parameter) > 0:
                    if parameter[0] == 0x3f: #
                        mnemonic = 'DECSET'
                        params = _parse_params(parameter[1:])
                        self.__screen.decset(params)
                    else:
                        mnemonic = 'SM'
                return not self.__visibility

            elif final == 0x6c: # l
                if len(parameter) > 0:
                    if parameter[0] == 0x3f: #
                        mnemonic = 'DECRST'
                        params = _parse_params(parameter[1:])
                        self.__screen.decrst(params)
                    else:
                        mnemonic = 'RM'
                return not self.__visibility

            elif final == 0x6d: # m
                mnemonic = 'SGR'
                params = _parse_params(parameter)
                self.__screen.sgr(params)

            elif final == 0x6e: # n
                return not self.__visibility

            elif final == 0x70: # p
                return not self.__visibility

            elif final == 0x72: # r
                if len(parameter) > 0:
                    if parameter[0] == 0x3f: # ?
                        param = ''.join([chr(c) for c in parameter])[1:]
                        params = [max(0, int(p)) for p in param.split(';')]
                        self.__screen.xt_rest(params)
                    else:
                        param = ''.join([chr(c) for c in parameter])
                        top, bottom = [max(0, int(p) - 1) for p in param.split(';')]
                        self.__screen.decstbm(top, bottom)
                else:
                    top, bottom = 0, self.__screen.height - 1
                    self.__screen.decstbm(top, bottom)

            elif final == 0x73: # s
                if len(parameter) > 0:
                    if parameter[0] == 0x3f: # ?
                        param = ''.join([chr(c) for c in parameter])[1:]
                        params = [max(0, int(p)) for p in param.split(';')]
                        self.__screen.xt_save(params)

            elif final == 0x78: # x
                return not self.__visibility

            else:
                pass
                #mnemonic = '[' + chr(final) + ']'
                #raise Exception(mnemonic)
        else:
            pass
            #mnemonic = '[' + str(intermediate) + ':' + chr(final) + ']'
            #raise Exception(mnemonic)

        return True 

    def handle_esc(self, context, prefix, final):
        if len(prefix) == 0:
            if final == 0x37: # 7
                self.__screen.cursor.save()
                return True
            elif final == 0x38: # 8
                self.__screen.cursor.restore()
                return True
            elif final == 0x44: # D
                self.__screen.ind()
            elif final == 0x45: # E
                self.__screen.nel()
            elif final == 0x48: # H
                self.__screen.hts()
            elif final == 0x4d: # M
                self.__screen.ri()
            elif final == 0x63: # c
                self.__screen.ris()
                return not self.__visibility # pass through
        elif prefix == [0x23]: # #
            if final == 0x38: # 8
                self.__screen.decaln()
            else:
                pass
        elif prefix == [0x28]: # (
            return True 
        elif prefix == [0x29]: # )
            return True 
        else:
            return True 
        return True

    def handle_char(self, context, c):
        screen = self.__screen
        if c < 0x20:
            if c == 0x00: #NUL
                pass
            elif c == 0x05: # ENQ
                screen.write(c)
                return not self.__visibility
            elif c == 0x07: # BEL
                screen.write(c)
            elif c == 0x08: # BS
                screen.bs()
            elif c == 0x09: # HT
                screen.ht()
            elif c == 0x0a: # NL
                screen.cr()
                screen.lf()
            elif c == 0x0b: # VT
                screen.lf()
            elif c == 0x0c: # FF
                screen.lf()
            elif c == 0x0d: # CR
                screen.cr()
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
            self.__screen.draw()

    def handle_resize(self, context, row, col):
        self.__screen.resize(row, col)



