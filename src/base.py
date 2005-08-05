# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: base.py 429 2005-07-21 20:55:07Z aafshar $
#Copyright (c) 2005 Ali Afshar aafshar@gmail.com

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


def set_application_instance(application):
    pidaobject._application = application

class pidaobject(object):
    NAME = 'pidaobject'

    def __init__(self, *args, **kw):
        self.pida = pidaobject._application
        #self.cb = self.pida

        self.do_action = self.pida.action
        self.do_evt = self.pida.evt
        self.do_edit = self.pida.edit
        
        self.prop_class_name = self.__class__.__name__
        self.prop_display_name = self.NAME
        
        self.do_init(*args, **kw)

    def __get_registry(self):
        return self.pida.registry

    prop_main_registry = property(__get_registry)

    def __get_plugins(self):
        return self.pida.plufins

    prop_loaded_plugins = property(__get_plugins)


    def __get_opt_plugins(self):
        return self.pida.OPTPLUGINS

    prop_optional_pluginlist = property(__get_opt_plugins)

    def __get_boss(self):
        return self.pida.boss

    prop_boss = property(__get_boss)


    def do_init(self, *args, **kw):
        pass

    def do_log(self, message, level):
        name = '%s;%s' % (self.prop_display_name, self.prop_class_name)
        self.pida.boss.do_log('log', '%s: %s' % (name, message), level)

    def do_log_debug(self, message):
        self.do_log(message, 20)

    def do_set_tooltip(self, widget, tiptext):
        self.pida.boss.tips.set_tip(widget, tiptext)

    def do_get_image(self, stockname):
        return self.pida.boss.icons.get_image(stockname)

    def do_get_button(self, stockname):
        return self.pida.boss.icons.get_button(stockname)

