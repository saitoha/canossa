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


import abc

################################################################################
#
# interfaces
#
# + Screen Layer API
#   - ICanossaScreen
#
# + Mode Handling
#   - IModeListener
#
# + Widgets
#
#   + ListBox
#     - IListbox
#     - IListboxListener
#
#   + InnerFrame
#     - IInnerFrame
#     - IInnerFrameListener
#
class IScreen:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def copyrect(self, s, srcx, srcy, width, height, destx=None, desty=None):
        raise NotImplementedError("IScreen::copyrect")

    @abc.abstractmethod
    def drawall(self, context):
        raise NotImplementedError("IScreen::drawall")

    @abc.abstractmethod
    def resize(self, row, col):
        raise NotImplementedError("IScreen::resize")

    @abc.abstractmethod
    def write(self, c):
        raise NotImplementedError("IScreen::write")

    @abc.abstractmethod
    def setlistener(self, listener):
        raise NotImplementedError("IScreen::setlistener")

class IScreenListener:

    @abc.abstractmethod
    def ontitlechanged(self, s):
        raise NotImplementedError("IScreenListener::ontitlechanged")

    @abc.abstractmethod
    def onmodeenabled(self, n):
        raise NotImplementedError("IScreenListener::onmodeenabled")

    @abc.abstractmethod
    def onmodedisabled(self, n):
        raise NotImplementedError("IScreenListener::onmodedisabled")

class IModeListener():

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def notifyenabled(self, n):
        raise NotImplementedError("IModeListener::notifyenabled")

    @abc.abstractmethod
    def notifydisabled(self, n):
        raise NotImplementedError("IModeListener::notifydisabled")

    @abc.abstractmethod
    def notifyimeon(self):
        raise NotImplementedError("IModeListener::notifyimeon")

    @abc.abstractmethod
    def notifyimeoff(self):
        raise NotImplementedError("IModeListener::notifyimeoff")

    @abc.abstractmethod
    def notifyimesave(self):
        raise NotImplementedError("IModeListener::notifyimesave")

    @abc.abstractmethod
    def notifyimerestore(self):
        raise NotImplementedError("IModeListener::notifyimerestore")

    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError("IModeListener::reset")

    @abc.abstractmethod
    def hasevent(self):
        raise NotImplementedError("IModeListener::hasevent")

    @abc.abstractmethod
    def getenabled(self):
        raise NotImplementedError("IModeListener::getenabled")


class IWidget():

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def id(self):
        raise NotImplementedError("IWidget::id")


class IListbox(IWidget):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def assign(self, a_list):
        raise NotImplementedError("IListbox::assign")

    @abc.abstractmethod
    def isempty(self):
        raise NotImplementedError("IListbox::isempty")

    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError("IListbox::reset")

    @abc.abstractmethod
    def movenext(self):
        raise NotImplementedError("IListbox::movenext")

    @abc.abstractmethod
    def moveprev(self):
        raise NotImplementedError("IListbox::moveprev")

    @abc.abstractmethod
    def jumpnext(self):
        raise NotImplementedError("IListbox::jumpnext")

    @abc.abstractmethod
    def draw(self, s):
        raise NotImplementedError("IListbox::draw")

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError("IListbox::close")

    @abc.abstractmethod
    def isshown(self):
        raise NotImplementedError("IListbox::isshown")

class IListboxListener():

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def oninput(self, popup, context, c):
        raise NotImplementedError("IListboxListener::oninput")

    @abc.abstractmethod
    def onselected(self, popup, index, text, remarks):
        raise NotImplementedError("IListboxListener::onselected")

    @abc.abstractmethod
    def onsettled(self, popup, context):
        raise NotImplementedError("IListboxListener::onsettled")

    @abc.abstractmethod
    def oncancel(self, popup, context):
        raise NotImplementedError("IListboxListener::oncancel")

    @abc.abstractmethod
    def onrepeat(self, popup, context):
        raise NotImplementedError("IListboxListener::onrepeat")


class IInnerFrame(IWidget):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError("IInnerFrame::close")

    @abc.abstractmethod
    def draw(self, output):
        raise NotImplementedError("IInnerFrame::draw")


class IInnerFrameListener():

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def onclose(self, iframe, context):
        raise NotImplementedError("IInnerFrameListener::onclose")


def test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    test()


