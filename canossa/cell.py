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

    __value = None

    attr = Attribute((0, 0x42))

    def __init__(self):
        self.__value = u' '

    def write(self, value, attr):
        self.__value = unichr(value)
        self.attr = attr.clone()

    def pad(self):
        self.__value = None 

    def combine(self, value):
        self.__value += unichr(value)

    def get(self):
        return self.__value

    def clear(self, attr):
        self.__value = u' '
        self.attr = attr.clone()

def test():
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
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

