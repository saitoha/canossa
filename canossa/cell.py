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

class Cell():

    """
    >>> from attribute import Attribute
    >>> cell = Cell() 
    >>> attr = Attribute()
    >>> print cell.get()
    >>> cell.write(0x34, attr)
    >>> print cell.get()
    >>> cell.clear(attr)
    >>> print cell.get()
    >>> cell.write(0x3042, attr)
    >>> print cell.get()
    >>> cell.pad()
    >>> print cell.get()
    >>> cell.write(0x09a4, attr)
    >>> print cell.get()
    >>> cell.combine(0x20DE)
    >>> print cell.get()
    >>> cell.combine(0x20DD)
    >>> print cell.get()
    >>> cell.combine(0x0308)
    >>> print cell.get()
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

