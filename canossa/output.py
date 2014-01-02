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
import thread
import logging
lock = thread.allocate_lock()

_CPR_NONE = 0
_CPR_ANSI = 1
_CPR_DEC = 2


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


def _generate_mock_parser(screen):
    import StringIO
    import tff

    canossa = Canossa(screen=screen, resized=False)
    outputcontext = tff.ParseContext(output=StringIO.StringIO(), handler=canossa, buffering=False)
    parser = tff.DefaultParser()
    parser.init(outputcontext)
    return parser


def _pack(s):
    result = 0
    for c in s:
        result = result << 8 | ord(c) 
    return result


class CSIHandlerTrait():

    def __init__(self):

        self._csi_map = {
            _pack('m'):   self._handle_sgr,
            _pack('H'):   self._handle_cup,
            _pack('h'):   self._handle_sm,
            _pack('l'):   self._handle_rm,
            _pack('?h'):  self._handle_decset,
            _pack('?l'):  self._handle_decrst,
            _pack('?s'):  self._handle_xtsave,
            _pack('?r'):  self._handle_xtrest,
            _pack('K'):   self._handle_el,
            _pack('J'):   self._handle_ed,
            _pack('G'):   self._handle_cha,
            _pack('@'):   self._handle_ich,
            _pack('A'):   self._handle_cuu,
            _pack('B'):   self._handle_cud,
            _pack('C'):   self._handle_cuf,
            _pack('D'):   self._handle_cub,
            _pack('L'):   self._handle_il,
            _pack('M'):   self._handle_dl,
            _pack('P'):   self._handle_dch,
            _pack('>c'):  self._handle_da2,
            _pack('d'):   self._handle_vpa,
            _pack('f'):   self._handle_hvp,
            _pack('g'):   self._handle_tbc,
            _pack('n'):   self._handle_dsr,
            _pack('?n'):  self._handle_decdsr,
            _pack('r'):   self._handle_decstbm,
            _pack('?$p'): self._handle_decrqm_dec,
            _pack('$p'):  self._handle_decrqm_ansi,
            _pack('"p'):  self._handle_decscl,
            _pack('!p'):  self._handle_decstr,
            _pack('x'):   self._handle_decreqtparm,
        }


    def _handle_sgr(self, context, parameter):
        """
        SGR - Select Graphics Rendition

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1;4;45mabc\x1b[mdef')
        """
        if not parameter:
            self.screen.reset_sgr()
        else:
            params = _param_generator(parameter)
            self.screen.sgr(params)
        return True


    def _handle_cup(self, context, parameter):
        """
        CUP - Cursor Position

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;5H')
        >>> screen.getyx()
        (4, 4)
        >>> parser.parse('\x1b[H')
        >>> screen.getyx()
        (0, 0)
        >>> parser.parse('\x1b[4H')
        >>> screen.getyx()
        (3, 0)
        >>> parser.parse('\x1b[5;H')
        >>> screen.getyx()
        (4, 0)
        >>> parser.parse('\x1b[;5H')
        >>> screen.getyx()
        (0, 4)
        """

        row, col = _param_generator(parameter, offset=-1, minarg=2)
        self.screen.cup(row, col)
        return True


    def _handle_sm(self, context, parameter):
        """
        SM - Set Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1h')
        """

        return not self._visibility


    def _handle_rm(self, context, parameter):
        """
        RM - Reset Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1l')
        """

        return not self._visibility


    def _handle_decset(self, context, parameter):
        """
        DECSET - DEC Specific Set Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1h')
        """

        params = _param_generator(parameter)
        self.screen.decset(params)
        return not self._visibility


    def _handle_decrst(self, context, parameter):
        """
        DECRST - DEC Specific Reset Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1l')
        """

        params = _param_generator(parameter)
        self.screen.decrst(params)
        return not self._visibility


    def _handle_xtsave(self, context, parameter):
        """
        XTSAVE(DEC) - Save DEC Specific Modes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1s')
        """
        params = _parse_params(parameter)
        self.screen.xt_save(params)
        return not self._visibility


    def _handle_xtrest(self, context, parameter):
        """
        XTREST(DEC) - Restore DEC Specific Modes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1r')
        """
        params = _parse_params(parameter)
        self.screen.xt_rest(params)
        return not self._visibility


    def _handle_el(self, context, parameter):
        """
        EL - Erase Line(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[K')
        """
        ps = _parse_params(parameter)[0]
        self.screen.el(ps)
        return True


    def _handle_ed(self, context, parameter):
        """
        ED - Erase Display

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[J')
        """
        ps = _parse_params(parameter)[0]
        self.screen.ed(ps)
        return True


    def _handle_cha(self, context, parameter):
        """
        CHA - Cursor Horizontal Absolute

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7G')
        >>> screen.getyx()
        (0, 6)
        """
        ps = _parse_params(parameter, offset=-1, minimum=1)[0]
        self.screen.cha(ps)
        return True


    def _handle_ich(self, context, parameter):
        """
        ICH - Insert Blank Character(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7@')
        """
        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.ich(ps)
        return True

    def _handle_cuu(self, context, parameter):
        """
        CUU - Cursor Up
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[10;10H')
        >>> screen.getyx()
        (9, 9)
        >>> parser.parse('\x1b[A')
        >>> screen.getyx()
        (8, 9)
        >>> parser.parse('\x1b[3A')
        >>> screen.getyx()
        (5, 9)
        >>> parser.parse('\x1b[10A')
        >>> screen.getyx()
        (0, 9)
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cuu(ps)
        return True


    def _handle_cud(self, context, parameter):
        """
        CUD - Cursor Down

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;10H')
        >>> screen.getyx()
        (4, 9)
        >>> parser.parse('\x1b[B')
        >>> screen.getyx()
        (5, 9)
        >>> parser.parse('\x1b[4B')
        >>> screen.getyx()
        (9, 9)
        >>> parser.parse('\x1b[40B')
        >>> screen.getyx()
        (23, 9)
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cud(ps)
        return True


    def _handle_cuf(self, context, parameter):
        """
        CUF - Cursor Forward

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;10H')
        >>> screen.getyx()
        (4, 9)
        >>> parser.parse('\x1b[C')
        >>> screen.getyx()
        (4, 10)
        >>> parser.parse('\x1b[4C')
        >>> screen.getyx()
        (4, 14)
        >>> parser.parse('\x1b[100C')
        >>> screen.getyx()
        (4, 79)
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cuf(ps)
        return True


    def _handle_cub(self, context, parameter):
        """
        CUB - Cursor Backward

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;10H')
        >>> screen.getyx()
        (4, 9)
        >>> parser.parse('\x1b[D')
        >>> screen.getyx()
        (4, 8)
        >>> parser.parse('\x1b[3D')
        >>> screen.getyx()
        (4, 5)
        >>> parser.parse('\x1b[10D')
        >>> screen.getyx()
        (4, 0)
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cub(ps)
        return True


    def _handle_il(self, context, parameter):
        """
        IL - Insert Line(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.il(ps)
        return True


    def _handle_dl(self, context, parameter):
        """
        DL - Delete Line(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7M')
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.dl(ps)
        return True


    def _handle_dch(self, context, parameter):
        """
        DCH - Delete Char(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7P')
        """

        #ps = _parse_params(parameter, minimum=1)[0]
        #self.screen.dch(ps)
        return True


    def _handle_da2(self, context, parameter):
        """
        DA2 - Secondary Device Attributes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[>c')
        """

        return False


    def _handle_vpa(self, context, parameter):
        """
        VPA - Vertical Position Absolute

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[4;4H')
        >>> screen.getyx()
        (3, 3)
        >>> parser.parse('\x1b[d')
        >>> screen.getyx()
        (0, 3)
        >>> parser.parse('\x1b[6d')
        >>> screen.getyx()
        (5, 3)
        >>> parser.parse('\x1b[100d')
        >>> screen.getyx()
        (23, 3)
        """

        ps = _parse_params(parameter, offset=-1)[0]
        self.screen.vpa(ps)
        return True


    def _handle_hvp(self, context, parameter):
        """
        HVP - Horizontal and Vertical Position

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;5f')
        >>> screen.getyx()
        (4, 4)
        >>> parser.parse('\x1b[f')
        >>> screen.getyx()
        (0, 0)
        >>> parser.parse('\x1b[4f')
        >>> screen.getyx()
        (3, 0)
        >>> parser.parse('\x1b[5;f')
        >>> screen.getyx()
        (4, 0)
        >>> parser.parse('\x1b[;5f')
        >>> screen.getyx()
        (0, 4)

        """

        row, col = _parse_params(parameter, offset=-1, minarg=2)
        self.screen.hvp(row, col)
        return True


    def _handle_tbc(self, context, parameter):
        """
        TBC - Tabstop Clear

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[g')
        """

        #ps = _parse_params(parameter)[0]
        #self.screen.tbc(ps)
        return not self._visibility


    def _handle_dsr(self, context, parameter):
        """
        DSR - Device Status Request

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[6n')
        >>> parser.parse('\x1b[n')
        """

        if len(parameter) == 1:
            if parameter[0] == 0x36: # 6
                y, x = self.screen.getyx()
                context.puts("\x1b[%d;%dR" % (y + 1, x + 1))
                return True
        return not self._visibility


    def _handle_decdsr(self, context, parameter):
        """
        DECDSR - DEC Specific Device Status Request

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?6n')
        >>> parser.parse('\x1b[6n')
        """

        if len(parameter) == 2:
            if parameter[1] == 0x36: # ?6
                y, x = self.screen.getyx()
                context.puts("\x1b[?%d;%dR" % (y + 1, x + 1))
                return True
        return not self._visibility


    def _handle_decstbm(self, context, parameter):
        """
        DECSTBM - Set Top and Bottom Margin

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[r')
        >>> screen.getyx()
        (0, 0)
        >>> parser.parse('\x1b[4;6r')
        >>> screen.getyx()
        (3, 0)
        """

        if parameter:
            top, bottom = _parse_params(parameter, offset=-1, minarg=2)
            self.screen.decstbm(top, bottom)
        else:
            top, bottom = 0, self.screen.height - 1
            self.screen.decstbm(top, bottom)
        return True


    def _handle_decrqm_ansi(self, context, parameter):
        """
        DECRQM(ANSI) - Request ANSI Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[$p')
        """

        return not self._visibility


    def _handle_decrqm_dec(self, context, parameter):
        """
        DECRQM(DEC) - Request DEC Private Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?$p')
        """

        return not self._visibility


    def _handle_decscl(self, context, parameter):
        """
        DECSCL - Set Conformance Level

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b["p')
        """

        return not self._visibility


    def _handle_decstr(self, context, parameter):
        """
        DECSTR - Soft Reset

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[!p')
        """

        self.screen.decstr()
        return True


    def _handle_decreqtparm(self, context, parameter):
        """
        DECREQTPARM - Request terminal parameters

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[x')
        """

        return not self._visibility


    def dispatch_csi(self, context, parameter, intermediate, final):
        if parameter and parameter[0] > 0x3b:
            key = parameter[0]
        else:
            key = 0
        key = reduce(lambda acc, x: acc << 8 | x, intermediate, key)
        key = key << 8 | final

        f = self._csi_map[key]
        return f(context, parameter)


class ESCHandlerTrait():

    def __init__(self):
            
        self._esc_map = {
            _pack('7'): self._esc_cursorsave,
            _pack('8'): self._esc_cursorrestore,
            _pack('D'): self._esc_ind,
            _pack('E'): self._esc_nel,
            _pack('H'): self._esc_hts,
            _pack('M'): self._esc_ri,
            _pack('c'): self._esc_ris,
            _pack('#3'): self._esc_decdhlt,
            _pack('#4'): self._esc_decdhlb,
            _pack('#5'): self._esc_decswl,
            _pack('#6'): self._esc_decdwl,
            _pack('#8'): self._esc_decaln,
        }


    def _esc_cursorsave(self):
        """
        DECSC - Save Cursor

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b7')
        """

        self.screen.cursor.save()
        return True


    def _esc_cursorrestore(self):
        """
        DECRC - Restore Cursor

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b8')
        """

        self.screen.cursor.save()
        return True


    def _esc_ind(self):
        """
        IND - Index

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1bD')
        """

        self.screen.ind()
        return True


    def _esc_nel(self):
        """
        NEL - Next Line

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1bE')
        """

        self.screen.nel()
        return True


    def _esc_hts(self):
        """
        HTS - Horizontal Tab Set

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1bH')
        """

        self.screen.hts()
        return True


    def _esc_ri(self):
        """
        RI - Reverse Index

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1bM')
        """

        self.screen.ri()
        return True


    def _esc_ris(self):
        """
        RIS - Hard Terminal Reset

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1bc')
        """

        self.screen.ris()
        return not self._visibility # pass through


    def _esc_decdhlt(self):
        """
        DECDHLT - Double Height Line (Top part)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b#3')
        """

        self.screen.decdhlt()
        return True


    def _esc_decdhlb(self):
        """
        DECDHLB - Double Height Line (Bottom part)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b#4')
        """

        self.screen.decdhlb()
        return True


    def _esc_decswl(self):
        """
        DECSWL - Single Width Line

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b#5')
        """

        self.screen.decswl()
        return True


    def _esc_decdwl(self):
        """
        DECDWL - Double Width Line

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b#6')
        """

        self.screen.decdwl()
        return True


    def _esc_decaln(self):
        """
        DECALN - Screen Alignment Pattern

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b#8')
        """

        self.screen.decaln()
        return True


    def dispatch_esc(self, context, intermediate, final):
        key = reduce(lambda acc, x: acc << 8 | x, intermediate, 0)
        key = key << 8 | final

        #elif intermediate == [0x28]: # (
        #    self.screen.set_g0(final)
        #    return True
        #elif intermediate == [0x29]: # )
        #    self.screen.set_g1(final)
        #    return True

        f = self._esc_map[key]

        return f()


class Canossa(tff.DefaultHandler,
              CSIHandlerTrait,
              ESCHandlerTrait):

    __cpr = False

    def __init__(self,
                 screen=None,
                 termenc="UTF-8",
                 termprop=None,
                 visibility=False,
                 resized=True):
        """
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> screen.getyx()
        (0, 0)
        >>> canossa = Canossa(screen=screen, resized=False)
        """

        if screen:
            self.screen = screen
        else:
            import sys
            from screen import Screen
            # make screen
            # get current position
            row, col, y, x = _get_pos_and_size(sys.stdin, sys.stdout)
            self.screen = Screen(row, col, y, x, termenc, termprop)

        self._visibility = visibility
        self.__cpr = False
        self._resized = resized

        CSIHandlerTrait.__init__(self)
        ESCHandlerTrait.__init__(self)


    def handle_csi(self, context, parameter, intermediate, final):
        """
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        """

        if self._resized:
            self._resized = False
            self.screen.adjust_cursor()
        try:
            return self.dispatch_csi(context, parameter, intermediate, final)

        except Exception, e:
            mnemonic = '[%s, %s, %s]' % (repr(parameter), repr(intermediate), chr(final)) 
            logging.error("handle_csi: %s" % mnemonic)
            logging.error("handle_csi: %s" % e)
        return True


    def handle_esc(self, context, intermediate, final):
        """
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        """


        if self._resized:
            self._resized = False
            self.screen.adjust_cursor()
        try:
            self.dispatch_esc(context, intermediate, final)
        except Exception, e:
            mnemonic = '[%s, %s]' % (repr(intermediate), chr(final)) 
            logging.error("handle_esc: %s" % mnemonic)
            logging.error("handle_esc: %s" % e)
        return True


    def handle_control_string(self, context, prefix, value):
        """
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b]0;abcde\\x1b\\\\')
        >>> parser.parse('\x1b]2;abcde\\x1b\\\\')
        >>> parser.parse('\x1b]Pq\\x1b\\\\')
        """

        if prefix == 0x5d: # ']'
            try:
                pos = value.index(0x3b)
            except ValueError:
                return False
            if pos == -1:
                return False
            elif pos == 0:
                num = [0]
            else:
                try:
                    num = value[:pos]
                except:
                    num = None
            if num:
                if num[0] == 0x30 or num[0] == 0x32:
                    arg = value[pos + 1:]
                    self.screen.settitle(u''.join([unichr(x) for x in arg]))
                    s = self.screen.gettitle()
                    if s:
                        value = num + [0x3b] + [ord(x) for x in s]
                        new_title = u"".join([unichr(c) for c in value])
                        #context.putu(u"\x1b]%s\x1b\\" % new_title)
                        return True

        return False


    def handle_char(self, context, c):
        """
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('abc\\x07def\\x0a\\x0d\\x0c\\x0e\\x0f')
        """

        if self._resized:
            self._resized = False
            self.screen.adjust_cursor()
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
            elif c == 0x00: # NUL
                pass
            elif c == 0x05: # ENQ
                return not self._visibility
            elif c == 0x07: # BEL
                pass
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
            screen.write(c)

        return True


    def handle_draw(self, context):
        if self._visibility:
            self.screen.drawall(context)
        #if self.__cpr != _CPR_NONE:
        #    if self.__cpr == _CPR_ANSI:
        #        self.__cpr = _CPR_NONE
        #        context.puts("\x1b[6n")
        #    elif self.__cpr == _CPR_DEC:
        #        self.__cpr = _CPR_NONE
        #        context.puts("\x1b[?6n")


    def handle_resize(self, context, row, col):
        lock.acquire()
        self._resized = True
        try:
            self.screen.resize(row, col)
        finally:
            lock.release()


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
