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


_ATTR_BOLD       = 1
_ATTR_UNDERLINED = 4
_ATTR_BLINK      = 5
_ATTR_INVERSE    = 7
_ATTR_INVISIBLE  = 8
_ATTR_FG         = 14 
_ATTR_BG         = 23 

class Attribute():

    __value = (0x100 << _ATTR_FG | 0x100 << _ATTR_BG, 0x42)

    def __init__(self, value = (0x100 << _ATTR_FG | 0x100 << _ATTR_BG, 0x42)):
        self.__value = value

    def draw(self, s):
        params = [0]
        value, charset = self.__value 
        for i in xrange(0, 8):
            if value & (2 << i):
                params.append(i) 

        fg = value >> _ATTR_FG & 0x1ff
        if fg == 0:
            pass
        elif fg < 8:
            params.append(30 + fg)
        elif fg == 0x100:
            params.append(39)
        else:
            params += [38, 5, fg]

        bg = value >> _ATTR_BG & 0x1ff
        if fg == 0:
            pass
        elif bg < 8:
            params.append(40 + bg)
        elif bg == 0x100:
            params.append(49)
        else:
            params += [48, 5, bg]
        s.write(u'\x1b(%c\x1b[%sm' % (charset, ';'.join([str(p) for p in params])))

    def clear(self):
        self.__value = (0x100 << _ATTR_FG | 0x100 << _ATTR_BG, 0x42)

    def get(self):
        return self.__value

    def set_charset(self, charset):
        value, old = self.__value
        self.__value = (value, charset)

    def set_sgr(self, pm):
        i = 0
        if len(pm) == 0:
            pm.append(0)
        value, charset = self.__value
        while i < len(pm):
            n = pm[i]
            if n == 0:
                value = 0x100 << _ATTR_FG | 0x100 << _ATTR_BG
            elif n == 1:
                value |= 2 << _ATTR_BOLD 
            elif n == 4:
                value |= 2 << _ATTR_UNDERLINED 
            elif n == 5:
                value |= 2 << _ATTR_BLINK 
            elif n == 7:
                value |= 2 << _ATTR_INVERSE 
            elif n == 8:
                value |= 2 << _ATTR_INVISIBLE 
            elif n == 21:
                value &= ~(2 << _ATTR_BOLD)
            elif n == 22:
                value &= ~(2 << _ATTR_BOLD | 2 << _ATTR_UNDERLINED)
            elif n == 24:
                value &= ~(2 << _ATTR_UNDERLINED)
            elif n == 25:
                value &= ~(2 << _ATTR_BLINK)
            elif n == 27:
                value &= ~(2 << _ATTR_INVERSE)
            elif n == 28:
                value &= ~(2 << _ATTR_VISIBLE)
            elif 30 <= n and n < 38:
                value = value & ~(0x1ff << _ATTR_FG) | (n - 30) << _ATTR_FG

            elif n == 38:
                i += 1
                n1 = pm[i]
                i += 1
                n2 = pm[i]
                if n1 == 5:
                    value = value & ~(0x1ff << _ATTR_FG) | (n2 << _ATTR_FG)
            elif n == 39:
                value = value & ~(0x1ff << _ATTR_FG) | (0x100 << _ATTR_FG)
            elif 40 <= n and n < 48:
                value = value & ~(0x1ff << _ATTR_BG) | (n - 40) << _ATTR_BG

            elif n == 48:
                i += 1
                n1 = pm[i]
                i += 1
                n2 = pm[i]
                if n1 == 5:
                    value = value & ~(0x1ff << _ATTR_BG) | (n2 << _ATTR_BG)
            elif n == 49:
                value = value & ~(0x1ff << _ATTR_BG) | (0x100 << _ATTR_BG)
            elif 90 <= n and n < 98:
                value = value & ~(0x1ff << _ATTR_FG) | (n - 90 + 8) << _ATTR_FG
            elif 100 <= n and n < 108:
                value = value & ~(0x1ff << _ATTR_BG) | (n - 100 + 8) << _ATTR_BG
            else:
               pass
               #logger.writeLine("SGR %d is ignored." % n)
            i += 1
        self.__value = (value, charset)

    def equeals(self, other):
        return self.__value == other.__value

    def __str__(self):
        import StringIO
        s = StringIO.StringIO()
        self.draw(s)
        return s.getvalue().replace("\x1b", "<ESC>")

def test():
    attr = Attribute() 
    print attr
    attr.set_sgr([0])
    print attr.equeals(Attribute())
    print attr
    attr.set_charset("A")
    print attr
    attr.set_sgr([0, 5, 6])
    print attr
    attr.set_sgr([7, 8])
    print attr
    attr.set_sgr([17, 18])
    print attr
    attr.set_sgr([38, 5, 200, 48, 5, 100])
    print attr

if __name__ == "__main__":
    print "attribute test."
    test()

