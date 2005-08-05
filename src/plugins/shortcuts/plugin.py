# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 352 2005-07-14 00:16:02Z gcbirzan $
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


import gtk

import pida.plugin as plugin
import ConfigParser
import os
import pida.base as base
#import tree
import gobject
import pida.gtkextra as gtkextra

class ShortcutTree(gtkextra.Tree):
    COLUMNS = [('name', gobject.TYPE_STRING,
                gtk.CellRendererText, True, 'text')]
    SCROLLABLE = False

    def populate(self, opts):
        self.clear()
        l = opts.sections()
        l.sort()
        for sect in l:
            self.add_item([sect])


class Window(gtk.Window):
    
    def __init__(self, cb):
        self.cb = cb
        gtk.Window.__init__(self)
        self.set_title('PIDA Shortcut Editor')
        self.set_transient_for(self.cb.mainwindow)



class Plugin(plugin.Plugin):
    NAME = "Shortcuts"

    def populate_widgets(self):
        # box for the lists
        ha = gtk.HBox()
        self.add(ha)
    
        self.sh_avail = ShortcutTree(self.cb)
        self.sh_avail.connect_select(self.cb_select_avail)
        ha.pack_start(self.sh_avail.win)

        vb = gtk.VBox()
        ha.pack_start(vb, padding=6)

        def addsep():
            sep = gtk.HSeparator()
            vb.pack_start(sep, expand=False, padding=4)

        hbn = gtk.HBox()
        vb.pack_start(hbn, expand=False)
        name_l = gtk.Label()
        name_l.set_markup('<b>Name</b>\nA name for your shortcut.')
        hbn.pack_start(name_l, expand=False)
        self.name = gtk.Entry()
        vb.pack_start(self.name)
       
        addsep()
        
        hbg = gtk.HBox()
        vb.pack_start(hbg, expand=False)
        glob_l = gtk.Label()
        glob_l.set_markup('<b>Glob</b>\n'
                          'A glob by which files will be filtered.\n'
                          'An empty glob implies *.*')
        hbg.pack_start(glob_l, expand=False)
        self.glob = gtk.Entry()
        vb.pack_start(self.glob)
        
        addsep()
 
        hbi = gtk.HBox()
        vb.pack_start(hbi, expand=False)
        icon_l = gtk.Label()
        icon_l.set_markup('<b>Icon</b>\n'
                          'The icon you wish to use.\n')
        hbi.pack_start(icon_l, expand=False)
        self.icon = gtkextra.FileButton(self.cb)
        vb.pack_start(self.icon)
        
        addsep()
 
        hbc = gtk.HBox()
        vb.pack_start(hbc, expand=False)
        com_l = gtk.Label()
        com_l.set_markup('<b>Command</b>\n'
                         'The command to be executed.')
        hbc.pack_start(com_l, expand=False)
        self.command = gtk.Entry()
        vb.pack_start(self.command)

        addsep()
 
        hbx = gtk.HBox()
        vb.pack_start(hbx, expand=False)
        ctx_l = gtk.Label()
        ctx_l.set_markup('<b>Contexts</b>\n'
                         'Which contexts the shortcut will appear.\n'
                         'Menus appear in the file browser.')
        hbx.pack_start(ctx_l, expand=False)
        
        self.ctx_ch = []
    
        self.ctx_ch.append(gtk.CheckButton(label='Menu for files.'))
        self.ctx_ch.append(gtk.CheckButton(label='Menu for directories.'))
        self.ctx_ch.append(gtk.CheckButton(label='Shell plugin toolbar.'))
        self.ctx_ch.append(gtk.CheckButton(label='Menu for positions in files.'))
        self.ctx_ch.append(gtk.CheckButton(label='Menu for strings.'))
        self.ctx_ch.append(gtk.CheckButton(label='Menu for urls (unused).'))

        for ch in self.ctx_ch:
            vb.pack_start(ch, expand=False)

        # Button Bar
        cb = gtk.HBox()
        vb.pack_start(cb, expand=False, padding=2)
        
        # separator
        sep = gtk.HSeparator()
        cb.pack_start(sep)
        
        # reset button
        revert_b = gtk.Button(stock=gtk.STOCK_REVERT_TO_SAVED)
        cb.pack_start(revert_b, expand=False)
        revert_b.connect('clicked', self.cb_revert)

        # cancel button
        delete_b = gtk.Button(stock=gtk.STOCK_DELETE)
        cb.pack_start(delete_b, expand=False)
        delete_b.connect('clicked', self.cb_delete)
        
        # reset button
        #reset_b = gtk.Button(stock=gtk.STOCK_UNDO)
        #cb.pack_start(reset_b, expand=False)
        #reset_b.connect('clicked', self.cb_reset)

        # apply button
        new_b = gtk.Button(stock=gtk.STOCK_NEW)
        cb.pack_start(new_b, expand=False)
        new_b.connect('clicked', self.cb_new)
        
        # save button
        save_b = gtk.Button(stock=gtk.STOCK_SAVE)
        cb.pack_start(save_b, expand=False)
        save_b.connect('clicked', self.cb_save)

    def do_init(self):
        self.shortcuts = Shortcuts(self.pida)


    def makewin(self):
        self.parent = None
        self.parent = Window(self.cb)
        self.parent.add(self.win)

    def show(self):
        self.refresh()
        self.makewin()
        self.parent.show()

    def refresh(self):
        self.shortcuts.load()
        self.sh_avail.populate(self.shortcuts)

    def hide(self):
        self.parent.hide()

    def save(self):
        args = self.get_info()
        n, s = args[:2]
        if n and s:
            self.shortcuts.set(*args)
            self.shortcuts.save()
        else:
            self.message('Name and Command must be entered.')
        self.refresh()
        self.cb.evt('resetshortcuts')
    
    def display(self, name):
        s, g, i, ctx = self.shortcuts.get(name)
        self.name.set_text(name)
        self.command.set_text(s)
        self.glob.set_text(g)
        self.icon.set_filename(i)
        for i, s in enumerate(ctx):
            self.ctx_ch[i].set_active(s == '1')

    def get_info(self):
        n = self.name.get_text()
        s = self.command.get_text()
        g = self.glob.get_text()
        if g == '':
            g = '*'
        i = self.icon.get_filename()
        ctx = []
        for ch in self.ctx_ch:
            ctx.append(int(ch.get_active()))
        return n, s, g, i, ctx

    def cb_select_avail(self, tv):
        self.display(self.sh_avail.selected(0))

    def cb_revert(self, *args):
        self.shortcuts.reset_defaults()
        self.refresh()

    def cb_new(self, *args):
        self.name.set_text('')
        self.command.set_text('')
        for ch in self.ctx_ch:
            ctx.set_active(False)

    def cb_delete(self, *args):
        name = self.sh_avail.selected(0)
        self.shortcuts.delete(name)
        self.refresh()
        #self.hide()

    def cb_save(self, *args):
        self.save()
   
    def evt_shortcuts(self):
        self.show()

    def load(self):
        self.shortcuts.load()

    def get_shortcuts(self):
        sects = self.shortcuts.sections()
        sects.sort()
        for sect in sects:
            l = list(self.shortcuts.get(sect))
            l.insert(0, sect)
            yield l


class Shortcuts(base.pidaobject):

    def __init__(self, cb):
        self.cb = cb
        self.config = ConfigParser.ConfigParser()
        #self.load()

    def set(self, name, s, glob, icon, ctx):
        if not self.config.has_section(name):
            self.config.add_section(name)
        self.config.set(name, 'command', s)
        self.config.set(name, 'glob', glob)
        self.config.set(name, 'icon', icon)
        self.config.set(name, 'file_context', ctx[0])
        self.config.set(name, 'directory_context', ctx[1])
        self.config.set(name, 'terminal_context', ctx[2])
        self.config.set(name, 'position_context', ctx[3])
        self.config.set(name, 'string_context', ctx[4])
        self.config.set(name, 'url_context', ctx[5])

    def delete(self, name):
        self.config.remove_section(name)
        self.save()

    def save(self):
        ''' Write the options file to the configured location. '''
        fn = self.cb.registry.files.shortcut_data.value()
        f = open(fn, 'w')
        self.config.write(f)
        f.close()

    def load(self):
        ''' Load the option file from the configured location. '''
        fn = self.cb.registry.files.shortcut_data.value()
        if fn and os.path.exists(fn):
            tempopts = ConfigParser.ConfigParser()
            f = open(fn, 'r')
            tempopts.readfp(f)
            f.close()
            for section in tempopts.sections():
                if tempopts.has_option(section, 'command'):
                    command = tempopts.get(section, 'command')
                    if tempopts.has_option(section, 'glob'):
                        glob = tempopts.get(section, 'glob')
                    else:
                        glob = '*'
                    if tempopts.has_option(section, 'icon'):
                        icon = tempopts.get(section, 'icon')
                    else:
                        icon = 'new'
                    ctxs = []
                    for ctx in ['file_context', 'directory_context',
                    'terminal_context', 'position_context', 'string_context',
                    'url_context']:
                        if tempopts.has_option(section, ctx):
                            ctxs.append(tempopts.get(section, ctx))
                        else:
                            ctxs.append('0')
                    self.set(section, command, glob, icon, ctxs)
        else:
            self.reset_defaults()

    def reset_defaults(self):
        DEF = [('Preview',
                self.cb.opts.get('commands', 'see'),
                '*', 'stock:preview',
                ['1', '0', '0', '0', '0', '0']),
               ('Python',
                self.cb.opts.get('commands', 'python'),
                '*.py', 'stock:python',
                ['1', '0', '1', '0', '0', '0']),
               ('Pager',
                self.cb.opts.get('commands', 'pager'),
                '*', 'stock:list',
                ['1', '0', '0', '0', '0', '0'])]
        
        self.config = ConfigParser.ConfigParser()
        for d in DEF:
            self.set(*d)
        self.save()

    def get(self,  name):
        return (self.config.get(name, 'command'),
                self.config.get(name, 'glob'),
                self.config.get(name, 'icon'),
                [self.config.get(name, 'file_context'),
                self.config.get(name, 'directory_context'),
                self.config.get(name, 'terminal_context'),
                self.config.get(name, 'position_context'),
                self.config.get(name, 'string_context'),
                self.config.get(name, 'url_context')])

    def sections(self):
        return self.config.sections()
    
if __name__ == '__main__':
    w = Window(None)
    w.show_all()
    gtk.main()

