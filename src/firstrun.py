# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: base.py 352 2005-07-14 00:16:02Z gcbirzan $
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
import os
import gtk
import base
from pida.configuration import registry

class IComponent(object):

    def get_sanity_errors(self):
        return None

class Vim(IComponent):
    LABEL = 'Vim'
    def get_sanity_errors(self):
        if registry.which('gvim'):
            return []
        else:
            return ['Gvim is not installed']
        
class Culebra(IComponent):
    LABEL = 'Culebra'

    def get_sanity_errors(self):
        errors = []
        try:
            import gtksourceview
        except ImportError:
            errors.append('Gtksourceview is not installed')
        return errors

EDITORS = {'vim':Vim(), 'culebra':Culebra()}

class FirstTimeWindow(base.pidaobject):

    def do_init(self):
        self.win = gtk.Window()
        self.win.set_title('First Time Wizard')
        self.win.connect('destroy', self.cb_done)
        self.win.set_position(gtk.WIN_POS_CENTER)

        hbox = gtk.HBox()
        self.win.add(hbox)

        logo = gtk.Image()
        logofrm = gtk.Frame()
        logofrm.add(logo)
        libdir = self.prop_main_registry.directories.shared.value()
        logofile = os.path.join(libdir, 'pidalogo.png')
        logo.set_from_file(logofile)
        hbox.pack_start(logofrm, padding = 8)
        
        box = gtk.VBox()
        hbox.pack_start(box, padding=8)

        s = ('It seems this is the first time '
            'you are running Pida.\n\nPlease select an editor:')

        box.pack_start(gtk.Label(s), expand=False, padding=8)
        
        radio = None

        for name in EDITORS:
            editor = EDITORS[name]
            ebox = gtk.HBox()
            box.pack_start(ebox, expand=False, padding=4)

            radio = gtk.RadioButton(radio, label=editor.LABEL)
            self.radio = radio
            ebox.pack_start(radio)

            cbox = gtk.VBox()
            label = gtk.Label()
            cbox.pack_start(label)
            ebox.pack_start(cbox, padding=4, expand=False)

            sanitybut = gtk.Button(label='Check')
            ebox.pack_start(sanitybut, expand=False, padding=1)
    
            sanitybut.connect('clicked', self.cb_sanity, editor, radio, label)
            self.cb_sanity(sanitybut, editor, radio, label)

        bbox = gtk.HBox()
        box.pack_start(bbox, expand=False, padding=4)


        cbut = gtk.Button(stock=gtk.STOCK_OK)
        cbut.connect('clicked', self.cb_done)
        bbox.pack_start(cbut, expand=True, padding=4)

    def show(self, fname):
        self.win.show_all()
        self.fname = fname
        gtk.main()

    def cb_sanity(self, button, component, radio, label):
        errs =  component.get_sanity_errors()
        if errs:
            radio.set_sensitive(False)
            s = '\n'.join(errs)
            label.set_markup('<span size="small" foreground="#c00000">'
                             '%s</span>' % s)
        else:
            label.set_markup('<span size="small" foreground="#00c000">'
                             'Okay to use</span>')
    
    def cb_done(self, *args):
        for radio in self.radio.get_group():
            if radio.get_active():
                editor = radio.get_label().lower()
                self.prop_main_registry.components.editor.set(editor)
                self.prop_main_registry.save()
                break
        if not os.path.exists(self.fname):
            f = open(self.fname, 'w')
            f. write('#Remove this to rerun the start wizard\n\n')
            f.close()
        self.hide()

    def hide(self):
        self.win.hide_all()
        self.win.destroy()
        gtk.main_quit()



