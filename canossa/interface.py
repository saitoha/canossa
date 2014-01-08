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

    def focus(self):
        raise NotImplementedError("IWidget::focus")

    def blur(self):
        raise NotImplementedError("IWidget::blur")

    def close(self):
        raise NotImplementedError("IWidget::close")

    def draw(self, output):
        raise NotImplementedError("IWidget::draw")

    def getlabel(self):
        raise NotImplementedError("IWidget::getlabel")


class IDesktop(IWidget):
    pass


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
