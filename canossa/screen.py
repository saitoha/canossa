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


import wcwidth
#try:
#    from cStringIO import StringIO
#except:
from StringIO import StringIO
import sys
#import logger

import sys, os, termios, select
from attribute import Attribute

#
# CSI ... ; ... R
#
def _get_pos():
    stdin = sys.stdin 
    stdout = sys.stdout
    stdin_fileno = stdin.fileno()
    vdisable = os.fpathconf(stdin_fileno, 'PC_VDISABLE')
    backup = termios.tcgetattr(stdin_fileno)
    new = termios.tcgetattr(stdin_fileno)
    new[3] &= ~(termios.ECHO | termios.ICANON)
    termios.tcsetattr(stdin_fileno, termios.TCSANOW, new)
    try:
        stdout.write("\x1b[6n")
        stdout.flush()
    except:
        pass
    def get_report():
        
        rfd, wfd, xfd = select.select([stdin_fileno], [], [], 0.5)
        if rfd:
            data = os.read(stdin_fileno, 1024)
            assert data[:2] == '\x1b['
            assert data[-1] == 'R'
            y, x = [int(n) - 1 for n in  data[2:-1].split(';')]
            return y, x
    try:
        return get_report()
    except:
        import time
        time.sleep(0.1)
        return get_report()
    finally:
        termios.tcsetattr(stdin_fileno, termios.TCSANOW, backup)

from cursor import Cursor
from line import Line

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

class SupportsWideCharacterTrait():

    _wcwidth = None

    def _setup_wcwidth(self, is_cjk=False):
        if is_cjk:
            self._wcwidth = wcwidth.mk_wcwidth
        else:
            self._wcwidth = wcwidth.mk_wcwidth_cjk

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
        for line in self.lines:
            line.clear(self.cursor.attr)
        self.lines = self._mainbuf
        for line in self.lines:
            line.resize(self.width)

    def switch_altbuf(self):
        self.lines = self._altbuf
        for line in self.lines:
            line.clear(self.cursor.attr)
        lines = self.lines
        if len(lines) > self.height:
            while len(lines) != self.height:
                lines.pop()
            for line in lines:
                line.resize(self.width)
        elif len(lines) < self.height:
            for line in lines:
                line.resize(self.width)
            while len(lines) != self.height:
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

    def decset(self, params):
        for param in params:
            if param == 1:
                pass # DECCKM
            elif param == 3:
                self.resize(self.height, 132)
                self.ris()
            elif param == 4:
                pass
            elif param == 6:
                self.decom = True
            elif param == 7:
                self.decawm = True
            elif param == 12:
                pass # cursor blink
            elif param == 25:
                self.dectcem = True
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
            else:
                # 1000 normal mouse tracking 
                # 1001 highlight mouse tracking 
                # 1002 button mouse tracking 
                # 1003 all mouse tracking 
                # 1005 UTF-8 mouse encoding 
                # 1006 SGR mouse encoding 
                # 1015 URXVT mouse encoding 
                # 2004 bracketed paste mode
                pass
                #import tff
                #raise tff.NotHandledException("DECSET %d" % param)

    def decrst(self, params):
        for param in params:
            if param == 1:
                pass # DECCKM
            elif param == 3:
                self.resize(self.height, 80)
                self.ris()
            elif param == 4:
                pass
            elif param == 6:
                self.decom = False
            elif param == 7:
                self.decawm = False
            elif param == 12:
                pass # cursor blink
            elif param == 25:
                self.dectcem = False
            elif param == 1000:
                pass
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
            elif param == 2004:
                pass # bracketed paste mode

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
        line = self.lines[self.cursor.row] 
        col = self.cursor.col
        if col < self.width:
            col += 1
            for stop in self._tabstop:
                if col <= stop:
                    self.cursor.col = stop 
                    break
            else:
                self.cursor.col = self.width - 1 
        else: 
            self.cursor.col = 0
        self.cursor.dirty = True

from interface import *

class ICanossaScreenImpl(ICanossaScreen):

    def drawrect(self, s, col, row, width, height):
        height = min(height, self.height)
        width =  min(width, self.width)
        for i in xrange(row, row + height):
            s.write("\x1b[%d;%dH" % (i + 1, col + 1))
            self.lines[i].draw(s, col, col + width)
        self.cursor.attr.draw(s)

    def getyx(self):
        cursor = self.cursor
        return cursor.row, cursor.col

    def draw(self, context):
        cursor = self.cursor
        s = StringIO()
        self.drawrect(s, 0, 0, self.width, self.height)
        cursor.draw(s)
        context.writestring(s.getvalue())

    def resize(self, row, col):
        lines = self.lines
        height = len(lines)
        if row < height:
            while row != len(lines):
                lines.pop()
            for line in lines:
                line.resize(col)
        elif row > height:
            for line in lines:
                line.resize(col)
            while row != len(lines):
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
        try:
            self.cursor.row, self.cursor.col = _get_pos()
            #sys.stdout.write("\x1b]2;%d-%d (%d, %d)\x1b\\" % (row, col, self.cursor.row, self.cursor.col))
        except:
            pass
        self.height = row
        self.width = col
        if self.cursor.row >= self.height:
            self.cursor.row = self.height - 1
        if self.cursor.col >= self.width:
            self.cursor.col = self.width - 1
        self._setup_tab()

    def write(self, c):
        row, col = self.cursor.row, self.cursor.col
        line = self.lines[row] 

        if col >= self.width:
            self._wrap()
            row, col = self.cursor.row, self.cursor.col
            line = self.lines[row] 

        line.dirty = True

        width = self._wcwidth(c)

        if width == 1: # normal (narrow) character
            if self.cursor.col >= self.width:
                self.cursor.col = self.width - 1
                col = self.cursor.col
            line.write(c, col, self.cursor.attr)
            self.cursor.dirty = True
            self.cursor.col += 1
            #if col > line.length() - 1:
            #    self.cursor.col = line.length() - 1
        elif width == 2: # wide character
            if self.cursor.col >= self.width - 1:
                self.cursor.col = self.width - 2
                col = self.cursor.col
            line.pad(col)
            line.write(c, col + 1, self.cursor.attr)
            self.cursor.dirty = True
            self.cursor.col += 2
            #if col > line.length() - 1:
            #    self.cursor.col = line.length() - 1
        elif width == 0: # combining character
            line.combine(c, col)

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


class Screen(ICanossaScreenImpl,
             MockScreenWithCursor,
             SupportsAnsiModeTrait,
             SupportsExtendedModeTrait,
             SupportsTabStopTrait,
             SupportsDoubleSizedTrait,
             SupportsWideCharacterTrait,
             SuuportsCursorPersistentTrait,
             SuuportsAlternateScreenTrait,
             SuuportsISO2022DesignationTrait):

    _saved_pos = None

    def __init__(self, row=24, col=80, y=0, x=0, is_cjk=False):
        self.height = row
        self.width = col
        self.cursor = Cursor(y, x)
        self.scroll_top = 0 
        self.scroll_bottom = self.height 

        self._setup_lines()
        self._setup_wcwidth()
        self._setup_altbuf()
        self._setup_tab()
        self._setup_charset()

    def _wrap(self):
        self.cursor.col = 0 
        if self.decawm:
            self.lf()

    def bs(self):
        if self.cursor.col >= self.width:
            self.cursor.col = self.width - 1

        if self.cursor.col <= 0:
            pass
        else:
            self.cursor.col -= 1
        self.cursor.dirty = True

    def lf(self):
        if self.cursor.col >= self.width:
            self._wrap() 
        self.cursor.row += 1
        if self.cursor.row >= self.scroll_bottom:
            for line in self.lines:
                line.dirty = True
            self.lines.insert(self.scroll_bottom, Line(self.width))
            self.lines.pop(self.scroll_top)
            self.cursor.row = self.scroll_bottom - 1 
        self.cursor.dirty = True

    def ind(self):
        self.lf()

    def nel(self):
        self.cr()
        self.lf()

    def ri(self):
        if self.cursor.row <= self.scroll_top:
            for line in self.lines:
                line.dirty = True
            self.lines.insert(self.scroll_top, Line(self.width))
            self.lines.pop(self.scroll_bottom)
            self.cursor.row = self.scroll_top 
        else:
            self.cursor.row -= 1
        self.cursor.dirty = True

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
        if self.decom:
            row += self.scroll_top
            top = self.scroll_top
            bottom = self.scroll_bottom
        else:
            top = 0
            bottom = self.height
        if row >= bottom:
            self.cursor.row = bottom - 1
        elif row < top:
            self.cursor.row = top
        else:
            self.cursor.row = row
        self.cursor.col = col
        self.cursor.dirty = True

    def ed(self, ps):
        if self.cursor.row >= self.height:
            self.cursor.row = self.height - 1
        if self.cursor.col >= self.width:
            self.cursor.col = self.width - 1
        if ps == 0:
            line = self.lines[self.cursor.row] 
            line.dirty = True
            for cell in line.cells[self.cursor.col:]:
                cell.clear(self.cursor.attr)
            if self.cursor.row < self.height:
                for line in self.lines[self.cursor.row + 1:]:
                    line.clear(self.cursor.attr)

        elif ps == 1:
            line = self.lines[self.cursor.row] 
            line.dirty = True
            for cell in line.cells[:self.cursor.col]:
                cell.clear(self.cursor.attr)
            if self.cursor.row > 0:
                for line in self.lines[:self.cursor.row]:
                    line.clear(self.cursor.attr)

        elif ps == 2:
            for line in self.lines:
                line.clear(self.cursor.attr)

        else:
            raise
  

    def decaln(self):
        for line in self.lines:
            line.dirty = True
            for cell in line.cells:
                cell.write(0x45, self.cursor.attr) # E
        self.scroll_top = 0 
        self.scroll_bottom = self.height 

    def ris(self):
        for line in self.lines:
            line.clear(self.cursor.attr)
        self.dectcem = True
        self.cursor.clear() 
        self._setup_tab()

    def sgr(self, pm):
        self.cursor.attr.set_sgr(pm)

    def ich(self, ps):
        ''' insert blank character(s) '''    
        row = self.cursor.row
        col = self.cursor.col
        if row >= self.scroll_bottom:
            self.cursor.row = self.scroll_bottom - 1
        elif row < self.scroll_top:
            self.cursor.row = self.scroll_top
        if col >= self.width:
            self.cursor.col = self.width - 1
        cells = self.lines[row].cells

        if col > 0 and cells[col - 1].get() == '\x00':
            col -= 1

        for i in xrange(0, ps):
            cell = cells.pop()
            cell.clear(self.cursor.attr)
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
        row = self.cursor.row
        lines = self.lines
        bottom = self.scroll_bottom
        for line in lines[row + ps:bottom]:
            line.dirty = True
        for x in xrange(0, ps):
            lines.insert(bottom, Line(self.width))
            lines.pop(row)

    def il(self, ps):
        row = self.cursor.row
        lines = self.lines
        bottom = self.scroll_bottom
        for line in lines[row:bottom - ps]:
            line.dirty = True
        for x in xrange(0, ps):
            lines.pop(bottom - 1)
            lines.insert(row, Line(self.width))

    def el(self, ps):
        line = self.lines[self.cursor.row] 
        if ps == 0:
            cells = line.cells[self.cursor.col:]
        elif ps == 1:
            cells = line.cells[:self.cursor.col]
        elif ps == 2:
            cells = line.cells
        else:
            raise
        line.dirty = True
        for cell in cells:
            cell.clear(self.cursor.attr) 

