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
# 
# ***** END LICENSE BLOCK *****

from cell import Cell

_LINE_TYPE_DHLT = 3
_LINE_TYPE_DHLB = 4
_LINE_TYPE_SWL  = 5
_LINE_TYPE_DWL  = 6

'''
    This module exports Line object, that consists of some cell objects.

       +-----+-----+-----+-...                   ...-+-----+
       |  A  |  B  |  C  |       ... ... ...         |     |
       +-----+-----+-----+-...                   ...-+-----+

    Ordinally, each cell contains a narrow character

    A wide character occupies 2 cells, the first cell contains '\0'

       +----+---------+-----+-...                   ...-+-----+
       | \0 | \x3042  |  C  |       ... ... ...         |     |
       +----+---------+-----+-...                   ...-+-----+
        <------------> <--->
         a wide char   char
'''

class SupportsDoubleSizedTrait():
    ''' For DECDWL/DECDHL support
    '''

    _type = _LINE_TYPE_SWL

    def set_swl(self):
        '''
        >>> line = Line(5)
        >>> line.set_swl()
        >>> line.type() == _LINE_TYPE_SWL
        True
        '''
        self._type = _LINE_TYPE_SWL
        self.dirty = True

    def set_dwl(self):
        '''
        >>> line = Line(5)
        >>> line.set_dwl()
        >>> line.type() == _LINE_TYPE_DWL
        True
        '''
        self._type = _LINE_TYPE_DWL
        self.dirty = True

    def set_dhlt(self):
        '''
        >>> line = Line(5)
        >>> line.set_dhlt()
        >>> line.type() == _LINE_TYPE_DHLT
        True
        '''
        self._type = _LINE_TYPE_DHLT
        self.dirty = True

    def set_dhlb(self):
        '''
        >>> line = Line(5)
        >>> line.set_dhlb()
        >>> line.type() == _LINE_TYPE_DHLB
        True
        '''
        self._type = _LINE_TYPE_DHLB
        self.dirty = True

    def is_normal(self):
        return self._type == _LINE_TYPE_SWL

    def type(self):
        '''
        >>> line = Line(5)
        >>> line.type() == _LINE_TYPE_SWL
        True
        '''
        return self._type

class SupportsWideTrait():
    ''' provides pad method. it makes the cell at specified position contain '\0'. '''

    def pad(self, pos):
        cell = self.cells[pos]
        cell.pad()

class SupportsCombiningTrait():
    ''' provides combine method. it combines specified character to the cell at specified position. '''

    def combine(self, value, pos):
        '''
        >>> from attribute import Attribute
        >>> line = Line(5)
        >>> attr = Attribute()
        >>> line.clear(attr._attrvalue)
        >>> line.write(0x40, 1, attr)
        >>> line.combine(0x300, 2)
        >>> print line
        <ESC>[0;39;49m<SP>@̀<SP><SP><SP>
        '''
        self.cells[max(0, pos - 1)].combine(value)

class Line(SupportsDoubleSizedTrait,
           SupportsWideTrait,
           SupportsCombiningTrait):

    def __init__(self, width):
        '''
        >>> line = Line(10)
        >>> len(line.cells)
        10
        >>> line.dirty
        True
        '''
        self.cells = [Cell() for cell in xrange(0, width)]
        self.dirty = True

    def length(self):
        '''
        >>> line = Line(19)
        >>> line.length()
        19
        '''
        return len(self.cells)

    def resize(self, col):
        '''
        >>> line = Line(14)
        >>> line.length()
        14
        >>> line.resize(9)
        >>> line.length()
        9
        >>> line.resize(0)
        >>> line.length()
        0
        >>> line.resize(20)
        >>> line.length()
        20
        '''
        width = len(self.cells)
        if col < width:
            self.cells = self.cells[:col]
        elif col > width:
            self.cells += [Cell() for cell in xrange(0, col - width)]
        self.dirty = True

    def clear(self, attrvalue):
        '''
        >>> from attribute import Attribute
        >>> line = Line(5)
        >>> line.clear(Attribute()._attrvalue)
        >>> print line
        <ESC>[0;39;49m<SP><SP><SP><SP><SP>
        '''
        if not self.dirty:
            self.dirty = True
        self.set_swl()
        for cell in self.cells:
            cell.clear(attrvalue)

    def write(self, value, pos, attr):
        '''
        >>> from attribute import Attribute
        >>> line = Line(5)
        >>> attr = Attribute()
        >>> line.clear(attr._attrvalue)
        >>> line.write(0x40, 0, attr)
        >>> print line
        <ESC>[0;39;49m@<SP><SP><SP><SP>
        >>> line.write(0x50, 0, attr)
        >>> print line
        <ESC>[0;39;49mP<SP><SP><SP><SP>
        >>> line.write(0x3042, 1, attr)
        >>> print line
        <ESC>[0;39;49mPあ<SP><SP><SP>
        '''
        if not self.dirty:
            self.dirty = True
        self.cells[pos].write(value, attr)

    def drawrange(self, s, left, right, cursor, lazy=False):
        '''
        >>> line = Line(5)
        >>> import StringIO
        >>> s = StringIO.StringIO()
        >>> from cursor import Cursor
        >>> line.drawrange(s, 3, 5, Cursor())
        >>> result = s.getvalue().replace("\x1b", "<ESC>")
        >>> result = result.replace("\x20", "<SP>")
        >>> print result
        <ESC>[0;39;49m<SP><SP>
        '''
        cells = self.cells
        attr = cursor.attr
        attr.draw(s)
        c = None
        if left > 0:
            cell = cells[left - 1]
            c = cell.get()
            if c is None:
                if False and lazy:
                    s.write(' ')
                    left += 1
                else:
                    s.write(u'\x08') # BS

        for cell in cells[left:right]:
            c = cell.get()
            if not c is None:
                if not attr.equals(cell.attr):
                    cell.attr.draw(s, attr)
                    attr.copyfrom(cell.attr)
                s.write(c)

        if not lazy:
            if c is None:
                for cell in cells[right:]:
                    c = cell.get()
                    if not c is None:
                        if not attr.equals(cell.attr):
                            cell.attr.draw(s, attr)
                            attr.copyfrom(cell.attr)
                        s.write(c)
                        break

    def drawall(self, s, cursor):
        self.dirty = False
        cells = self.cells
        s.write(u"\x1b#%d" % self._type)
        attr = cursor.attr
        attr.draw(s)
        c = None
        for cell in cells:
            c = cell.get()
            if not c is None:
                if not attr.equals(cell.attr):
                    cell.attr.draw(s, attr)
                    attr.copyfrom(cell.attr)
                s.write(c)
        if c is None:
            for cell in cells[right:]:
                c = cell.get()
                if not c is None:
                    if not attr.equals(cell.attr):
                        cell.attr.draw(s, attr)
                        attr.copyfrom(cell.attr)
                    s.write(c)
                    break

    def __str__(self):
        '''
        >>> line = Line(5)
        >>> print line
        <ESC>[0;39;49m<SP><SP><SP><SP><SP>
        '''
        import StringIO, codecs
        import locale
        from cursor import Cursor
        language, encoding = locale.getdefaultlocale()
        cursor = Cursor()
        s = codecs.getwriter(encoding)(StringIO.StringIO())
        self.drawrange(s, 0, len(self.cells), cursor)
        result = s.getvalue().replace("\x1b", "<ESC>")
        result = result.replace("\x20", "<SP>")
        result = result.replace("\x00", "<NUL>")
        return result

def test():
    """
    >>> from attribute import Attribute
    >>> line = Line(10)
    >>> attr = Attribute()
    >>> print line
    <ESC>[0;39;49m<SP><SP><SP><SP><SP><SP><SP><SP><SP><SP>
    >>> line.clear(attr._attrvalue)
    >>> print line
    <ESC>[0;39;49m<SP><SP><SP><SP><SP><SP><SP><SP><SP><SP>
    >>> line.write(0x40, 0, attr)
    >>> line.write(0x50, 0, attr)
    >>> print line
    <ESC>[0;39;49mP<SP><SP><SP><SP><SP><SP><SP><SP><SP>
    >>> line.write(0x40, 1, attr)
    >>> print line
    <ESC>[0;39;49mP@<SP><SP><SP><SP><SP><SP><SP><SP>
    >>> line.pad(2)
    >>> line.write(0x3042, 3, attr)
    >>> print line
    <ESC>[0;39;49mP@あ<SP><SP><SP><SP><SP><SP>
    >>> line.write(0x30, 5, attr)
    >>> print line
    <ESC>[0;39;49mP@あ<SP>0<SP><SP><SP><SP>
    """
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

