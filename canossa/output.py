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


class Canossa(tff.DefaultHandler):

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

        self.__visibility = visibility
        self.__cpr = False
        self._resized = resized

        def _pack(s):
            result = 0
            for c in s:
                result = result << 8 | ord(c) 
            return result

        self._map = {
            _pack('m'): self.handle_sgr,
            _pack('H'): self.handle_cup,
            _pack('h'): self.handle_sm,
            _pack('l'): self.handle_rm,
            _pack('?h'): self.handle_decset,
            _pack('?l'): self.handle_decrst,
            _pack('?s'): self.handle_xtsave,
            _pack('?r'): self.handle_xtrest,
            _pack('K'): self.handle_el,
            _pack('J'): self.handle_ed,
            _pack('G'): self.handle_cha,
            _pack('@'): self.handle_ich,
            _pack('A'): self.handle_cuu,
            _pack('B'): self.handle_cud,
            _pack('C'): self.handle_cuf,
            _pack('D'): self.handle_cud,
            _pack('L'): self.handle_il,
            _pack('M'): self.handle_dl,
            _pack('P'): self.handle_dch,
            _pack('>c'): self.handle_da2,
            _pack('d'): self.handle_vpa,
            _pack('f'): self.handle_hvp,
            _pack('g'): self.handle_tbc,
            _pack('n'): self.handle_dsr,
            _pack('?n'): self.handle_decdsr,
            _pack('r'): self.handle_decstbm,
            _pack('?$'): self.handle_decrqm_dec,
            _pack('$'): self.handle_decrqm_ansi,
            _pack('"p'): self.handle_decscl,
            _pack('!p'): self.handle_decstr,
            _pack('x'): self.handle_decreqtparm,
        }

    def handle_sgr(self, context, parameter):
        """
        SGR - Select Graphics Rendition

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1;4;45mabc\x1b[mdef')
        >>> screen.lines[0]
        
        """

        if not parameter:
            self.screen.reset_sgr()
        else:
            params = _param_generator(parameter)
            self.screen.sgr(params)
        return True


    def handle_cup(self, context, parameter):
        """
        CUP - Cursor Position

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[5;5H')
        >>> screen.getyx()
        (4, 4) 
        """

        row, col = _param_generator(parameter, offset=-1, minarg=2)
        self.screen.cup(row, col)
        return True


    def handle_sm(self, context, parameter):
        """
        SM - Set Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1h')
        """

        return not self.__visibility


    def handle_rm(self, context, parameter):
        """
        RM - Reset Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1h')
        """

        return not self.__visibility


    def handle_decset(self, context, parameter):
        """
        DECSET - DEC Specific Set Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1h')
        """

        params = _param_generator(parameter)
        self.screen.decset(params)
        return not self.__visibility


    def handle_decrst(self, context, parameter):
        """
        DECRST - DEC Specific Reset Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[1h')
        """

        params = _param_generator(parameter)
        self.screen.decrst(params)
        return not self.__visibility


    def handle_xtsave(self, context, parameter):
        """
        XTSAVE(DEC) - Save DEC Specific Modes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1s')
        """
        params = _parse_params(parameter)
        self.screen.xt_save(params)
        return not self.__visibility


    def handle_xtrest(self, context, parameter):
        """
        XTREST(DEC) - Restore DEC Specific Modes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[?1r')
        """
        params = _parse_params(parameter)
        self.screen.xt_rest(params)
        return not self.__visibility


    def handle_el(self, context, parameter):
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


    def handle_ed(self, context, parameter):
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


    def handle_cha(self, context, parameter):
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


    def handle_ich(self, context, parameter):
        """
        ICH - Insert Blank Character(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7@')
        >>> screen.getyx()
        (0, 6)
        """
        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.ich(ps)
        return True

    def handle_cuu(self, context, parameter):
        """
        CUU - Cursor Up
        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7A')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cuu(ps)
        return True


    def handle_cud(self, context, parameter):
        """
        CUD - Cursor Down

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7B')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cud(ps)
        return True


    def handle_cuf(self, context, parameter):
        """
        CUF - Cursor Forward

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cuf(ps)
        return True


    def handle_cub(self, context, parameter):
        """
        CUB - Cursor Backward

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7D')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.cub(ps)
        return True


    def handle_il(self, context, parameter):
        """
        IL - Insert Line(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.il(ps)
        return True


    def handle_dl(self, context, parameter):
        """
        DL - Delete Line(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.dl(ps)
        return True


    def handle_dch(self, context, parameter):
        """
        DCH - Delete Char(s)

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, minimum=1)[0]
        self.screen.dch(ps)
        return True


    def handle_da2(self, context, parameter):
        """
        DA2 - Secondary Device Attributes

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7C')
        >>> screen.getyx()
        """

        return False


    def handle_vpa(self, context, parameter):
        """
        VPA - Vertical Position Absolute

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7d')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter, offset=-1)[0]
        self.screen.vpa(ps)
        return True


    def handle_hvp(self, context, parameter):
        """
        HVP - Horizontal and Vertical Position

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[7f')
        >>> screen.getyx()
        """

        row, col = _parse_params(parameter, offset=-1, minarg=2)
        self.screen.hvp(row, col)
        return True


    def handle_tbc(self, context, parameter):
        """
        TBC - Tabstop Clear

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[g')
        >>> screen.getyx()
        """

        ps = _parse_params(parameter)[0]
        self.screen.tbc(ps)
        return True


    def handle_dsr(self, context, parameter):
        """
        DSR - Device Status Request

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[g')
        >>> screen.getyx()
        """

        if len(parameter) == 1:
            if parameter[0] == 0x36: # 6
                if not intermediate:
                    y, x = self.screen.getyx()
                    context.puts("\x1b[%d;%dR" % (y + 1, x + 1))
                    return True
        return not self.__visibility


    def handle_decdsr(self, context, parameter):
        """
        DECDSR - DEC Specific Device Status Request

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[g')
        >>> screen.getyx()
        """

        if len(parameter) == 2:
            if intermediate[1] == 0x36: # ?6
                if not intermediate:
                    y, x = self.screen.getyx()
                    context.puts("\x1b[?%d;%dR" % (y + 1, x + 1))
                    return True
        return not self.__visibility


    def handle_decstbm(self, context, parameter):
        """
        DECSTBM - Set Top and Bottom Margin

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[r')
        >>> screen.getyx()
        """

        if parameter:
            top, bottom = _parse_params(parameter, offset=-1, minarg=2)
            self.screen.decstbm(top, bottom)
        else:
            top, bottom = 0, self.screen.height - 1
            self.screen.decstbm(top, bottom)
        return True


    def handle_decrqm_ansi(self, context, parameter):
        """
        DECRQM(ANSI) - Request ANSI Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[>p')
        >>> screen.getyx()
        """

        return not self.__visibility


    def handle_decrqm_dec(self, context, parameter):
        """
        DECRQM(DEC) - Request DEC Private Mode

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b[>p')
        >>> screen.getyx()
        """

        return not self.__visibility


    def handle_decscl(self, context, parameter):
        """
        DECSCL - Set Conformance Level

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b["p')
        >>> screen.getyx()
        """

        return not self.__visibility


    def handle_decstr(self, context, parameter):
        """
        DECSTR - Soft Reset

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b["p')
        >>> screen.getyx()
        """

        self.screen.decstr()
        return True


    def handle_decreqtparm(self, context, parameter):
        """
        DECREQTPARM - Request terminal parameters

        >>> from screen import MockScreenWithCursor
        >>> screen = MockScreenWithCursor()
        >>> parser = _generate_mock_parser(screen)
        >>> parser.parse('\x1b["p')
        >>> screen.getyx()
        """

        return not self.__visibility


    def handle_csi(self, context, parameter, intermediate, final):

        if self._resized:
            self._resized = False
            self.screen.adjust_cursor()
        try:
            if parameter and parameter[0] > 0x3b:
                key = parameter[0]
            else:
                key = 0
            key = reduce(lambda acc, x: acc << 8 | x, intermediate, key)
            key = key << 8 | final

            if key in self._map:
                self._map[key](context, parameter)

            else:
                mnemonic = '[' + chr(final) + ']'
                logging.error("mnemonic: %s" % mnemonic)

        except Exception, e:
            mnemonic = '[' + chr(final) + ']'
            logging.exception("handle_csi: %s" % mnemonic)
        return True

    def handle_esc(self, context, intermediate, final):
        if self._resized:
            self._resized = False
            self.screen.adjust_cursor()
        if not intermediate:
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
        #elif intermediate == [0x28]: # (
        #    self.screen.set_g0(final)
        #    return True
        #elif intermediate == [0x29]: # )
        #    self.screen.set_g1(final)
        #    return True
        else:
            return True
        return True

    def handle_control_string(self, context, prefix, value):
        if prefix == 0x5d: # ']'
            try:
                pos = value.index(0x3b)
            except ValueError:
                return
            if pos == -1:
                return
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
            elif c == 0x00: #NUL
                pass
            elif c == 0x05: # ENQ
                screen.write(c)
                return not self.__visibility
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
                pass
        else:
            screen.write(c)

        return True

    def handle_draw(self, context):
        if self.__visibility:
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
