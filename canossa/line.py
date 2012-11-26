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

from attribute import Attribute
from cell import Cell

""" 
This module exports Line object, that consists of some cell objects.

   +-----+-----+-----+-...                   ...-+-----+
   |  A  |  B  |  C  |       ... ... ...         |     |
   +-----+-----+-----+-...                   ...-+-----+

Ordinally, each cell contains a narrow character

>>> line = Line(10)
>>> attr = Attribute()
>>> print line
<ESC>#5<ESC>(B<ESC>[0m<SP><SP><SP><SP><SP><SP><SP><SP><SP><SP>
>>> line.clear(attr)
>>> print line
<ESC>#5<ESC>(B<ESC>[0;39;49m<SP><SP><SP><SP><SP><SP><SP><SP><SP><SP>
>>> line.write(0x40, 0, attr)
>>> line.write(0x50, 0, attr)
>>> print line
<ESC>#5<ESC>(B<ESC>[0;39;49mP<SP><SP><SP><SP><SP><SP><SP><SP><SP>
>>> line.write(0x40, 1, attr)
>>> print line
<ESC>#5<ESC>(B<ESC>[0;39;49mP@<SP><SP><SP><SP><SP><SP><SP><SP>

A wide character occupies 2 cells, the first cell contains '\0'

   +----+---------+-----+-...                   ...-+-----+
   | \0 | \x3042  |  C  |       ... ... ...         |     |
   +----+---------+-----+-...                   ...-+-----+
    <------------> <--->
     a wide char   char 

>>> line.write(0x3042, 2, attr)
>>> print line
<ESC>#5<ESC>(B<ESC>[0;39;49mP@あ<SP><SP><SP><SP><SP><SP><SP>
>>> line.write(0x30, 5, attr)
>>> print line
<ESC>#5<ESC>(B<ESC>[0;39;49mP@あ<SP><SP>0<SP><SP><SP><SP>
"""

_LINE_TYPE_DHLT = 3
_LINE_TYPE_DHLB = 4
_LINE_TYPE_SWL  = 5
_LINE_TYPE_DWL  = 6

class SupportsDoubleSizedTrait():
    ''' For DECDWL/DECDHL support '''

    _type = _LINE_TYPE_SWL

    def set_swl(self):
        self._type = _LINE_TYPE_SWL
        self.dirty = True

    def set_dwl(self):
        self._type = _LINE_TYPE_DWL
        self.dirty = True

    def set_dhlt(self):
        self._type = _LINE_TYPE_DHLT
        self.dirty = True

    def set_dhlb(self):
        self._type = _LINE_TYPE_DHLB
        self.dirty = True

    def type(self):
        return self._type

class SupportsWideTrait():
    ''' provides pad method. it makes the cell at specified position contain '\0'. '''

    def pad(self, pos):
        self.cells[pos].pad()

class SupportsCombiningTrait():
    ''' provides combine method. it combines specified character to the cell at specified position. '''

    def combine(self, value, pos):
        self.cells[max(0, pos - 1)].combine(value)

class Line(SupportsDoubleSizedTrait,
           SupportsWideTrait,
           SupportsCombiningTrait):

    def __init__(self, width):
        self.cells = [Cell() for cell in xrange(0, width)]
        self.dirty = True

    def length(self):
        return len(self.cells)

    def resize(self, col):
        width = len(self.cells)
        if col < width:
            self.cells = self.cells[:col]
        elif col > width:
            self.cells += [Cell() for cell in xrange(0, col - width)]
        self.dirty = True

    def clear(self, attr):
        self.dirty = True
        self._type = _LINE_TYPE_SWL
        for cell in self.cells:
            cell.clear(attr)

    def write(self, value, pos, attr):
        self.cells[pos].write(value, attr)

    def draw(self, s, left, right):
        self.dirty = False
        attr = None 
        cells = self.cells
        c = None
        s.write(u"\x1b#%d" % self._type)
        if left > 0:
            c = cells[left - 1].get()
            if c is None:
                s.write(u'\x08') # BS
                left -= 1
        for cell in cells[left:right]:
            c = cell.get()
            if not c is None:
                if attr != cell.attr:
                    attr = cell.attr
                    Attribute(attr).draw(s)
                s.write(c)
        if c is None:
            for cell in cells[right:]:
                c = cell.get()
                if not c is None:
                    if attr != cell.attr:
                        attr = cell.attr
                        Attribute(attr).draw(s)
                    s.write(c)
                    break

    def __str__(self):
        import StringIO, codecs
        import locale
        language, encoding = locale.getdefaultlocale()
        s = codecs.getwriter(encoding)(StringIO.StringIO())
        self.draw(s, 0, len(self.cells)) 
        result = s.getvalue().replace("\x1b", "<ESC>")
        result = result.replace("\x20", "<SP>")
        result = result.replace("\x00", "<NUL>")

if __name__ == "__main__":
    import doctest
    doctest.testmod()

