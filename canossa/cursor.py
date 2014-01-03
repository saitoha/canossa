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

from attribute import Attribute


class Cursor():

    col = 0
    row = 0
    dirty = True
    attr = None
    _backup = None

    def __init__(self, y=0, x=0, attr=Attribute()):
        self.col = x
        self.row = y
        self.dirty = True
        self.attr = attr
        self._backup = None

    def clear(self):
        self.col = 0
        self.row = 0
        self.dirty = True
        self.attr.clear()

    def save(self):
        self._backup = Cursor(self.row, self.col, self.attr.clone())

    def restore(self):
        if self._backup:
            self.col = self._backup.col
            self.row = self._backup.row
            self.attr = self._backup.attr
            self._backup = None

    def draw(self, s):
        s.write("\x1b[%d;%dH" % (self.row + 1, self.col + 1))
        self.dirty = False

    def setyx(self, y, x):
        self.row = y
        self.col = x

    def getyx(self):
        return self.row, self.col

    def __str__(self):
        import StringIO
        s = StringIO.StringIO()
        self.draw(s)
        return s.getvalue().replace("\x1b", "<ESC>")


def test():
    """
    >>> cursor = Cursor()
    >>> print cursor
    <ESC>[1;1H
    >>> cursor.clear()
    >>> print cursor
    <ESC>[1;1H
    >>> cursor.setyx(10, 20)
    >>> print cursor
    <ESC>[11;21H
    >>> print cursor.getyx()
    (10, 20)
    >>> cursor.save()
    >>> cursor.setyx(24, 15)
    >>> print cursor
    <ESC>[25;16H
    >>> cursor.clear()
    >>> print cursor
    <ESC>[1;1H
    >>> cursor.restore()
    >>> print cursor
    <ESC>[11;21H
    """
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
