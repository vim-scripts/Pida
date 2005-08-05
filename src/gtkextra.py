# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: gtkextra.py 469 2005-07-27 22:24:01Z aafshar $
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
import shelve
import fnmatch
import gobject
import base

POPUP_CONTEXTS = ['file', 'dir', 'terminal', 'position', 'string', 'url']

class Tree(base.pidaobject):
    """
    A custom treeview subclass that is used throughout Pida.
    
    @cvar COLUMNS: The columns that will be created for this table
    @type COLUMNS: a C{list} of C{(name, data_type, renderer_type, visibility,
        display_field) tuples}

    @cvar SCROLLABLE: Whether the tree will be placed in a scrolled window.
    @type SCROLLABLE: C{boolean}
    """
    COLUMNS = [('name', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup')]
    SCROLLABLE = True
    XPAD = 0
    YPAD = 1

    def do_init(self, *args):
        self.model = gtk.TreeStore(*[l[1] for l in self.COLUMNS])
        self.view = gtk.TreeView(self.model)
        self.view.set_headers_visible(False)
        self.view.set_rules_hint(True)
        self.view.set_enable_search(False)
        self.win = gtk.VBox()

        self.toolbar = gtk.HBox()
        self.win.pack_start(self.toolbar, expand=False, padding=4)

        if self.SCROLLABLE:
            sw = gtk.ScrolledWindow()
            self.win.pack_start(sw)
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.add(self.view)
        else:
            self.win.pack_start(self.view)
        i = 0
        for (name, typ, rendtype, vis, attr) in self.COLUMNS:
            if vis:
                renderer = rendtype()
                renderer.set_property('ypad', self.YPAD)
                renderer.set_property('xpad', self.XPAD)
                attrdict = {attr:i}
                column = gtk.TreeViewColumn(name, renderer, **attrdict)
                #column.set_expand(False)
                column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
                self.view.append_column(column)
            i = i + 1

        self.r_cb_activated = None
        self.view.connect('row-activated', self.cb_activated)
        self.r_cb_selected = None
        self.view.connect('cursor-changed', self.cb_selected)
        self.r_cb_rightclick = None
        self.view.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.view.connect('button-press-event', self.cb_butpress)


        self.view.columns_autosize()
        self.init()
    
    def init(self):
        """ Called by the constructor, for overriding. """
        pass

    def add_item(self, data, parent=None):
        """ Add an item to the tree view's model. """
        return self.model.append(parent, data)

    def clear(self):
        """ Clear the View. """
        self.model.clear()

    def connect_select(self, cb):
        """ Connect the external single-click handler. """
        self.r_cb_selected = cb

    def connect_activate(self, cb):
        """ Connect the external activate handler. """
        self.r_cb_activated = cb

    def connect_rightclick(self, cb):
        """ Connect the external right-click handler. """
        self.r_cb_rightclick = cb

    def cb_activated(self, *args):
        if self.l_cb_activated(*args) and self.r_cb_activated:
            self.r_cb_activated(*args)

    def cb_butpress(self, source, event):
        return
        if event.button == 3:
            if len(self.model):
                path = self.view.get_dest_row_at_pos(int(event.x),
                                                            int(event.y))
                if path:
                    ite = self.model.get_iter(path)
                    self.cb_rightclick(ite, event.time)

    def cb_selected(self, *args):
        if self.l_cb_selected(*args) and self.r_cb_selected:
            self.r_cb_selected(*args)

    def cb_rightclick(self, *args):
        if self.l_cb_rightclick(*args) and self.r_cb_rightclick:
            self.r_cb_rightclick(*args)

    def l_cb_activated(self, tv, path, arg):
        return True

    def l_cb_selected(self, *args):
        return True

    def l_cb_rightclick(self, ite, time):
        return True

    def update(self):
        self.view.set_model(self.model)

    def selected(self, column):
        ite = self.selected_iter()
        if ite:
            return self.get(ite, column)

    def selected_iter(self):
        path = self.view.get_cursor()[0]
        if path:
            return self.model.get_iter(path)
        
    def selected_path(self):
        return self.view.get_cursor()[0]

    def get(self, niter, column):
        return self.model.get_value(niter, column)

    def set(self, niter, column, value):
        self.model.set_value(niter, column, value)

    def toggle_expand(self, path):
        niter = self.model.get_iter(path)
        if self.model.iter_has_child(niter):
            if self.view.row_expanded(path):
                self.view.collapse_row(path)
            else:
                self.view.expand_row(path, False)

class FolderDialog(base.pidaobject, gtk.FileChooserDialog):
    TITLE = 'Select Directory'
    ACTION = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER

    def do_init(self, responsecb):
        gtk.FileChooserDialog.__init__(self, title=self.TITLE,
                                             parent=None,
                                             action=self.ACTION,
                                             buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                                                gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.connect('response', responsecb)

    def connect_widgets(self):
        pass

class FolderButton(base.pidaobject, gtk.HBox):
    DTYPE = FolderDialog

    def do_init(self):
        gtk.HBox.__init__(self)
        self.entry = gtk.Entry()
        self.pack_start(self.entry)
        self.but = self.do_get_button('open')
        self.but.connect('clicked', self.cb_open)
        self.pack_start(self.but, expand=False)
        self.dialog = None

    def update(self):
        self.entry.set_text(self.dialog.get_filename())

    def show(self):
        if not self.dialog:
            self.dialog = self.DTYPE(self.cb_response)
            self.dialog.connect('destroy', self.cb_destroy)
        entrytext = self.entry.get_text()
        if entrytext:
            self.dialog.set_filename(self.entry.get_text())
        self.dialog.set_transient_for(self.pida.mainwindow)
        self.dialog.show()

    def cb_response(self, d, resp):
        self.dialog.hide()
        if resp == gtk.RESPONSE_ACCEPT:
            self.update()
        
    def cb_destroy(self, *args):
        self.dialog.destroy()
        self.dialog = None

    def cb_open(self, *args):
        self.show()

    def get_filename(self):
        return self.entry.get_text()

    get_text = get_filename

    def set_filename(self, fn):
        self.entry.set_text(fn)

    set_text = set_filename

class FileDialog(FolderDialog):
    TITLE = 'Select File'
    ACTION = gtk.FILE_CHOOSER_ACTION_OPEN

    def connect_widgets(self):
        def cb(*args):
            self.response(1)
        self.connect('file-activated', cb)
        
class FileButton(FolderButton):
    DTYPE = FileDialog

class Winparent(base.pidaobject, gtk.Window):
    def do_init(self, child):
        gtk.Window.__init__(self)
# Only set transient if on_top is true, or not defined.
        if child.registry.on_top.value():
            self.set_transient_for(self.pida.mainwindow)
        self.childplug = child
        self.show()
        child.win.reparent(self)
        self.connect('destroy', child.attach)

class Transient(base.pidaobject):

    def do_init(self):
        self.win = gtk.VBox()

        self.tb = gtk.HBox()
        self.win.pack_start(self.tb, expand=False)
        
        self.close_but = self.do_get_button('close')
        eb = gtk.EventBox()
        eb.add(self.close_but)
        self.tb.pack_start(eb, expand=False)
        self.do_set_tooltip(eb, 'Close mini window')
        self.close_but.connect('clicked', self.cb_close_but)

        self.label = gtk.Label()
        self.tb.pack_start(self.label, expand=False)

        sep = gtk.HSeparator()
        self.tb.pack_start(sep)

        self.frame = gtk.VBox()
        self.win.pack_start(self.frame)#, expand=False)
        self.populate_widgets()
    
    def populate_widgets(self):
        pass    

    def show(self, label):
        self.label.set_markup(label)
        self.win.show_all()

    def hide(self):
        self.win.hide_all()

    def cb_close_but(self, *args):
        self.hide()

class Messagebox(Transient):

    def populate_widgets(self):
        self.display_label = gtk.Label()
        self.display_label.set_line_wrap(True)
        self.frame.pack_start(self.display_label, expand=False)
        self.id = 0

    def message(self, msg):
        self.id = self.id + 1
        self.display_label.set_label(msg)
        self.show('Message (%s)' % self.id)
       
class Questionbox(Messagebox):
    
    def populate_widgets(self):
        Messagebox.populate_widgets(self)
        self.hbar = gtk.HBox()
        self.frame.pack_start(self.hbar, expand=False)
        self.entry = gtk.Entry()
        self.hbar.pack_start(self.entry)
        eb = gtk.EventBox()
        self.tb.pack_start(eb, expand=False)
        self.submit = self.do_get_button('apply')
        eb.add(self.submit)
        self.do_set_tooltip(eb, 'ok')

    def question(self, msg, callback):
        def cb(*args):
            self.submit.disconnect(self.qid)
            self.hide()
            callback(self.entry.get_text().strip())
        self.entry.set_text('')
        self.entry.connect('activate', cb)
        self.qid = self.submit.connect('clicked', cb)
        self.display_label.set_label(msg)
        self.show('Question (%s)' % self.id)
        self.entry.grab_focus()
        
class Optionbox(Messagebox):
    def populate_widgets(self):
        Messagebox.populate_widgets(self)
        self.entry = gtk.combo_box_new_text()
        self.frame.pack_start(self.entry)
        self.submit = self.do_get_button('apply', 12)
        self.tb.pack_start(self.submit, expand=False)

    def option(self, msg, options, callback):
        def cb(*args):
            self.hide()
            callback(self.entry.get_active_text())
        self.entry.get_model().clear()
        for i in options:
            self.entry.append_text(i)
        self.entry.set_active(0)
        self.submit.connect('clicked', cb)
        self.display_label.set_label(msg)
        self.show('Option (%s)' % self.id)
 
class Toolbar(base.pidaobject):

    def do_init(self, *args):
        self.win = gtk.HBox()

    def add_button(self, stock, callback, tooltip='None Set!', cbargs=[]):
        evt = gtk.EventBox()
        but = self.do_get_button(stock)
        evt.add(but)
        self.do_set_tooltip(evt, tooltip)
        but.connect('clicked', callback, *cbargs)
        self.win.pack_start(evt, expand=False, padding=0)
        return but

    def add_separator(self):
        sep = gtk.VSeparator()
        self.win.pack_start(sep, padding=0, expand=False)

    def pack_start(self, *args, **kw):
        self.win.pack_start(*args, **kw)

    def show(self):
        self.win.show_all()

class Sepbar(base.pidaobject):
    def do_init(self):
        self.win = gtk.EventBox()
        exp = gtk.HSeparator()
        self.win.add(exp)
        self.win.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.win.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.win.connect('button-press-event', self.cb_press)
        self.cb_rclick = None
        self.cb_dclick = None

    def cb_press(self, eb, event):
        if event.button == 3:
            if self.cb_rclick:
                self.cb_rclick(event)
        elif event.type == gtk.gdk._2BUTTON_PRESS:
            if self.cb_dclick:
                self.cb_dclick(event)

    def connect(self, rclick, dclick):
        self.cb_rclick = rclick
        self.cb_dclick = dclick

class Popup(base.pidaobject):

    def do_init(self, *args):
        self.menu = gtk.Menu()
        self.init(*args)
    
    def add_item(self, icon, text, cb, cbargs):
        mi = gtk.MenuItem()
        self.menu.append(mi)
        mi.connect('activate', cb, cbargs)
        hb = gtk.HBox()
        mi.add(hb)
        im = self.do_get_image(icon)
        hb.pack_start(im, expand=False, padding=4)
        lb = gtk.Label(text)
        hb.pack_start(lb, expand=False)
        return mi

    def add_separator(self):
        ms = gtk.SeparatorMenuItem()
        self.menu.append(ms)

    def popup(self, time):
        self.menu.show_all()
        self.menu.popup(None, None, None, 3, time)

    def clear(self):
        for mi in self.menu.get_children():
            self.menu.remove(mi)

    def init(self, *args):
        pass


class ContextGenerator(base.pidaobject):

    def do_init(self, name):
        self.name = name
        self.aargs = []

    def generate(self):
        for sect in self.cb.shortcuts.get_shortcuts():
            name, command, glob, icon, ctx = sect
            for i, ct in enumerate(ctx):
                if POPUP_CONTEXTS[i] == self.name and ct == '1':
                    gmatch = None
                    if self.aargs:
                        gmatch = fnmatch.fnmatch(self.aargs[0], glob)
                    if not self.aargs or gmatch:
                        com, args = self.cargs_from_line(command)
                        if icon.startswith('stock:'):
                            icon = icon.replace('stock:', '', 1)
                        mi = self.add_item(icon, name,
                            self.cb_activate, [com, args, self.aargs])
                        mi.stock_icon = icon

    def cargs_from_line(self, line):
        el = line.split(' ')
        command = el.pop(0)
        el.insert(0, 'pida')
        return command, el

    def cb_activate(self, source, command, args, filename):
        pass

class ContextPopup(ContextGenerator, Popup):

    def do_init(self, name):
        Popup.do_init(self, name)
        ContextGenerator.do_init(self, name)
        

    def popup(self, filename, time):
        self.aargs = [filename]
        self.clear()
        self.generate()
        self.add_separator()
        self.add_item('configure', 'Configure these shortcuts.',
                       self.cb_configure, [])
        Popup.popup(self, time)

    def add_item(self, stock, name, cb, cbargs):
        if stock.startswith('stock:'):
            stock = stock.replace('stock:', '', 1)
        mi = Popup.add_item(self, stock, name, cb, cbargs)
        return mi

    def cb_configure(self, *args):
        self.cb.action_showshortcuts()

    def cb_openvim(self, menu, (filename,)):
        self.cb.action_openfile(filename)

    def cb_activate(self, menu, (command, args, aargs)):
        #assume just filename for now
        fn = aargs.pop()
        if '<fn>' in args:
            args[args.index('<fn>')] = fn
        else:
            args.append(fn)
        print command, args, aargs 
        args.pop(0)
        args.insert(0, command)
        commandline = ' '.join(args)
        self.do_action('newterminal', commandline, icon=menu.stock_icon)

class PositionPopup(ContextPopup):
    def popup(self, filename, line, time):
        self.aargs = [filename]
        self.clear()
        self.add_item('break', 'Add breakpoint here', self.cb_setbp,
                      [filename, line])
        self.add_item('clear', 'Clear breakpoint here', self.cb_clrbp,
                      [filename, line])
        self.generate()
        self.add_separator()
        self.add_item('configure', 'Configure these shortcuts.',
                       self.cb_configure, [])
        Popup.popup(self, time)
    
    def cb_setbp(self, menu, (filename, line)):
        self.cb.evt('breakpointset', line, filename)

    def cb_clrbp(self, menu, (filename, line)):
        self.cb.evt('breakpointclear', line, filename)

class ContextToolbar(ContextGenerator, Toolbar):
    #def __init__(self, cb, name):
    #    Toolbar.__init__(self, cb)
    #    ContextGenerator.__init__(self, cb, name)
    
    def do_init(self, name):
        Toolbar.do_init(self, name)
        ContextGenerator.do_init(self, name)
        self.generate()

    def add_item(self, stock, name, cb, cbargs):
        if stock.startswith('stock:'):
            stock = stock.replace('stock:', '', 1)
        return self.add_button(stock, cb, name, cbargs)

    def cb_activate(self, button, command, args, aargs):
        print button.stock_icon
        self.cb.action_newterminal(command, args, icon=button.stock_icon)
       
    def refresh(self):
        self.clear()
        self.generate()

    def clear(self):
        for i in self.win.get_children():
            self.win.remove(i)

class Icons(base.pidaobject):

    def do_init(self):
        icon_file = self.prop_main_registry.files.icon_data.value()
        self.d = shelve.open(icon_file, 'r')
        self.cs = gtk.gdk.COLORSPACE_RGB
    
    def get(self, name, *args):
        if name not in  self.d:
            name = 'new'
        d, a = self.d[name]
        pb = gtk.gdk.pixbuf_new_from_data(d, self.cs, *a)
        return pb

    def get_image(self, name, *size):
        im = gtk.Image()
        im.set_from_pixbuf(self.get(name))
        return im

    def get_button(self, name, *asize):
        ic = self.get_image(name)
        but = gtk.ToolButton(icon_widget=ic)
        return but
        
class IPWindow(object):
    def __init__(self, pb):
        self.pb = pb
        self.rw = gtk.Window()
        self.rw.realize()
        self.rw.add_events(gtk.gdk.PROPERTY_CHANGE_MASK)
        self.rw.connect('property-notify-event', self.cb_r)

    def reset(self, id):
        self.ww = gtk.gdk.window_foreign_new(id)

    def write(self, property, value, ptype=32):
        self.ww.property_change(property, gtk.gdk.SELECTION_TYPE_STRING,
                                ptype,
                                gtk.gdk.PROP_MODE_REPLACE,
                                value)

    def connect(self):
        self.write('connect', [self.rw.window.xid])
        
    def cb_r(self, window, ev):
        if hasattr(ev, 'atom'):
            message = self.rw.window.property_get(ev.atom, pdelete=True)
            if message and ('%s' % ev.atom)[0].islower():
                self.do(ev, message)

    def do(self, ev, message):
                self.pre_do()
                c = 'do_%s' % ev.atom
                v = message[-1]
                if hasattr(self.pb, c):
                    getattr(self.pb, c)(v)
                else:
                    getattr(self, c, lambda a: None)(v)

    def pre_do(self):
        pass

    def do_connect(self, cid):
        self.reset(long(cid[0]))

    def get_lid(self):
        return self.rw.window.xid

    def get_rid(self):
        return self.ww.xid
