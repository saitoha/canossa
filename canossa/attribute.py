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


_ATTR_BOLD = 1        # 00000000 00000000 00000000 00000010
_ATTR_UNDERLINED = 4  # 00000000 00000000 00000000 00010000
_ATTR_BLINK = 5       # 00000000 00000000 00000000 00100000
_ATTR_INVERSE = 7     # 00000000 00000000 00000000 10000000
_ATTR_INVISIBLE = 8   # 00000000 00000000 00000001 00000000
_ATTR_NRC = 9         # 00000000 00000000 00011110 00000000
_ATTR_FG = 13         # 00000000 00111111 11100000 00000000
_ATTR_BG = 22         # 01111111 11000000 00000000 00000000

_ATTR_DEFAULT = 0x100 << _ATTR_FG | 0x100 << _ATTR_BG

_NRC_REVERSE_MAP = ['B', '0', 'A', '4',
                    'C', 'R', 'Q', 'K',
                    'Y', 'E', '6', 'Z',
                    'H', '7', '=', '5']
_NRC_MAP = {}

for key, value in enumerate(_NRC_REVERSE_MAP):
    _NRC_MAP[ord(value)] = key


class Attribute():

    """
    >>> attr = Attribute()
    >>> print attr
    <ESC>[0;39;49m
    >>> attr.set_sgr([0])
    >>> print attr.equals(Attribute())
    True
    >>> print attr
    <ESC>[0;39;49m
    >>> attr.set_charset(0x41)
    True
    >>> print attr
    <ESC>[0;39;49m
    >>> attr.set_sgr(x for x in (0, 5, 6))
    >>> print attr
    <ESC>[0;5;39;49m
    >>> attr.set_sgr(x for x in (7, 8))
    >>> print attr
    <ESC>[0;5;7;8;39;49m
    >>> attr.set_sgr(x for x in (17, 18))
    >>> print attr
    <ESC>[0;5;7;8;39;49m
    >>> attr.set_sgr(x for x in (38, 5, 200, 48, 5, 100))
    >>> print attr
    <ESC>[0;5;7;8;38;5;200;48;5;100m
    """

    _attrvalue = _ATTR_DEFAULT
    defaultvalue = _ATTR_DEFAULT

    def __init__(self, value=_ATTR_DEFAULT):
        self._attrvalue = value

    def setvalue(self, attrvalue):
        self._attrvalue = attrvalue

    def draw(self, s, attr=None):
        params = [0]
        if attr:
            value_current = attr._attrvalue
        else:
            value_current = _ATTR_DEFAULT
        value = self._attrvalue
        for i in (1, 4, 5, 7, 8):
            if value & (1 << i) != 0:
                params.append(i)

        fg = value >> _ATTR_FG & 0x1ff
        if fg == 0x100:
            params.append(39)
        elif fg < 8:
            params.append(30 + fg)
        elif fg < 16:
            params.append(90 + fg - 8)
        else:
            params.extend((38, 5, fg))

        bg = value >> _ATTR_BG & 0x1ff
        if bg == 0x100:
            params.append(49)
        elif bg < 8:
            params.append(40 + bg)
        elif bg < 16:
            params.append(100 + bg - 8)
        else:
            params.extend((48, 5, bg))

        charset = value & 0xf << 9
        if charset != value_current & 0xf << _ATTR_NRC:
            if len(_NRC_REVERSE_MAP) > charset:
                s.write(u'\x1b(%c' % _NRC_REVERSE_MAP[charset])
        s.write(u'\x1b[%sm' % ';'.join([str(p) for p in params]))

    def clear(self):
        self._attrvalue = _ATTR_DEFAULT

    def clone(self):
        return Attribute(self._attrvalue)

    def copyfrom(self, attr):
        self._attrvalue = attr._attrvalue

    def getbcevalue(self):
        value = self._attrvalue
        return value & (0x3ffff << _ATTR_FG)

    def getdefaultvalue(self):
        return _ATTR_DEFAULT

    def set_charset(self, charset):
        value = self._attrvalue
        try:
            code = _NRC_MAP[charset]
            self._attrvalue = value & ~(0xf << _ATTR_NRC) | (code << _ATTR_NRC)
        except ValueError:
            return False
        return True

    def set_sgr(self, pm):
        i = 0
        value = self._attrvalue
        for n in pm:
            if n < 10:
                if n == 0:
                    value = _ATTR_DEFAULT
                elif n == 1:
                    value |= 1 << _ATTR_BOLD
                elif n == 4:
                    value |= 1 << _ATTR_UNDERLINED
                elif n == 5:
                    value |= 1 << _ATTR_BLINK
                elif n == 7:
                    value |= 1 << _ATTR_INVERSE
                elif n == 8:
                    value |= 1 << _ATTR_INVISIBLE
            elif n < 30:
                if n == 21:
                    value &= ~(1 << _ATTR_BOLD)
                elif n == 22:
                    value &= ~(1 << _ATTR_BOLD | 1 << _ATTR_UNDERLINED)
                elif n == 24:
                    value &= ~(1 << _ATTR_UNDERLINED)
                elif n == 25:
                    value &= ~(1 << _ATTR_BLINK)
                elif n == 27:
                    value &= ~(1 << _ATTR_INVERSE)
                elif n == 28:
                    value &= ~(1 << _ATTR_INVISIBLE)
            elif n < 40:
                if n == 38:
                    if pm.next() == 5:
                        value &= ~(0x1ff << _ATTR_FG)
                        value |= pm.next() << _ATTR_FG
                elif n == 39:
                    value &= ~(0x1ff << _ATTR_FG)
                    value |= 0x100 << _ATTR_FG
                else:
                    assert n != 0
                    value &= ~(0x1ff << _ATTR_FG)
                    value |= (n - 30) << _ATTR_FG
            elif n < 50:
                if n == 48:
                    if pm.next() == 5:
                        value &= ~(0x1ff << _ATTR_BG)
                        value |= pm.next() << _ATTR_BG
                elif n == 49:
                    value &= ~(0x1ff << _ATTR_BG)
                    value |= 0x100 << _ATTR_BG
                else:
                    value &= value & ~(0x1ff << _ATTR_BG)
                    value |= (n - 40) << _ATTR_BG
            elif 90 <= n and n < 98:
                value &= ~(0x1ff << _ATTR_FG)
                value |= (n - 90 + 8) << _ATTR_FG
            elif 100 <= n and n < 108:
                value &= ~(0x1ff << _ATTR_BG)
                value |= (n - 100 + 8) << _ATTR_BG
            #logger.writeLine("SGR %d is ignored." % n)
            i += 1
        self._attrvalue = value

    def equals(self, other):
        return self._attrvalue == other._attrvalue

    def __str__(self):
        from StringIO import StringIO
        s = StringIO()
        self.draw(s)
        return s.getvalue().replace("\x1b", "<ESC>")


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    print "attribute test."
    test()
