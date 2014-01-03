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

class Cell():

    """
    >>> from attribute import Attribute
    >>> cell = Cell()
    >>> attr = Attribute()
    >>> cell.get()
    u' '
    >>> cell.write(0x34, attr)
    >>> cell.get()
    u'4'
    >>> cell.clear(attr._attrvalue)
    >>> cell.get()
    u' '
    >>> cell.write(0x3042, attr)
    >>> cell.get()
    u'\u3042'
    >>> cell.pad()
    >>> cell.get()
    >>> cell.write(0x09a4, attr)
    >>> cell.get()
    u'\u09a4'
    >>> cell.combine(0x20DE)
    >>> cell.get()
    u'\u09a4\u20de'
    >>> cell.combine(0x20DD)
    >>> cell.get()
    u'\u09a4\u20de\u20dd'
    >>> cell.combine(0x0308)
    >>> cell.get()
    u'\u09a4\u20de\u20dd\u0308'
    """

    _value = None
    _combine = None

    def __init__(self):
        self._value = 0x20
        self.attr = Attribute()

    def write(self, value, attr):
        self._value = value
        self.attr.copyfrom(attr)

    def pad(self):
        self._value = None

    def combine(self, value):
        if self._combine:
            self._combine += unichr(value)
        else:
            self._combine = unichr(value)

    def get(self):
        if self._value is None:
            return None
        result = unichr(self._value)
        if self._combine is None:
            return result
        return result + self._combine

    def clear(self, attrvalue):
        self._value = 0x20
        self._combine = None
        self.attr.setvalue(attrvalue)

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
