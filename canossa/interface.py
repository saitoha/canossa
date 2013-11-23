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

    def copyrect(self, s, srcx, srcy, width, height, destx=None, desty=None):
        raise NotImplementedError("IScreen::copyrect")

    def drawall(self, context):
        raise NotImplementedError("IScreen::drawall")

    def resize(self, row, col):
        raise NotImplementedError("IScreen::resize")

    def write(self, c):
        raise NotImplementedError("IScreen::write")

    def setlistener(self, listener):
        raise NotImplementedError("IScreen::setlistener")

class IScreenListener:

    def ontitlechanged(self, s):
        raise NotImplementedError("IScreenListener::ontitlechanged")

    def onmodeenabled(self, n):
        raise NotImplementedError("IScreenListener::onmodeenabled")

    def onmodedisabled(self, n):
        raise NotImplementedError("IScreenListener::onmodedisabled")

class IModeListener():

    def notifyenabled(self, n):
        raise NotImplementedError("IModeListener::notifyenabled")

    def notifydisabled(self, n):
        raise NotImplementedError("IModeListener::notifydisabled")

    def notifyimeon(self):
        raise NotImplementedError("IModeListener::notifyimeon")

    def notifyimeoff(self):
        raise NotImplementedError("IModeListener::notifyimeoff")

    def notifyimesave(self):
        raise NotImplementedError("IModeListener::notifyimesave")

    def notifyimerestore(self):
        raise NotImplementedError("IModeListener::notifyimerestore")

    def reset(self):
        raise NotImplementedError("IModeListener::reset")

    def hasevent(self):
        raise NotImplementedError("IModeListener::hasevent")

    def getenabled(self):
        raise NotImplementedError("IModeListener::getenabled")


class IWidget():

    def close(self):
        raise NotImplementedError("IWidget::close")

    def draw(self, output):
        raise NotImplementedError("IWidget::draw")


class IListbox(IWidget):

    def assign(self, a_list):
        raise NotImplementedError("IListbox::assign")

    def isempty(self):
        raise NotImplementedError("IListbox::isempty")

    def reset(self):
        raise NotImplementedError("IListbox::reset")

    def movenext(self):
        raise NotImplementedError("IListbox::movenext")

    def moveprev(self):
        raise NotImplementedError("IListbox::moveprev")

    def jumpnext(self):
        raise NotImplementedError("IListbox::jumpnext")

    def isshown(self):
        raise NotImplementedError("IListbox::isshown")

class IListboxListener():

    def oninput(self, popup, context, c):
        raise NotImplementedError("IListboxListener::oninput")

    def onselected(self, popup, index, text, remarks):
        raise NotImplementedError("IListboxListener::onselected")

    def onsettled(self, popup, context):
        raise NotImplementedError("IListboxListener::onsettled")

    def oncancel(self, popup, context):
        raise NotImplementedError("IListboxListener::oncancel")

    def onrepeat(self, popup, context):
        raise NotImplementedError("IListboxListener::onrepeat")


class IInnerFrame(IWidget):
    pass

class IInnerFrameListener():

    def onclose(self, iframe, context):
        raise NotImplementedError("IInnerFrameListener::onclose")


def test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    test()
