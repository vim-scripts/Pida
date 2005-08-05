# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 450 2005-07-24 01:15:29Z aafshar $
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
#import tree
import os
import gobject
import pida.gtkextra as gtkextra
import pida.configuration.registry as registry

try:
    import bike
    from bike.parsing import fastparser
except ImportError:
    bike = fastparser = None
    print ('Python refactring functionality is not available. '
           'If you wish to use these features please install '
           'bicycle repair man (eg "apt-get install bicyclerepair").')

brmctx = None

def brm():
    global brmctx
    if not brmctx:
        brmctx = bike.init().brmctx
    return brmctx

class DefTree(gtkextra.Tree):
    COLUMNS = [('name', gobject.TYPE_STRING, None, False, None),
               ('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('line', gobject.TYPE_INT, None, False, None),
               ('column', gobject.TYPE_INT, None, False, None)]

    def populate(self, rootnodes, parent=None):
        for node in rootnodes:
            b = self.beautify(node)
            col = node.getLine(0).index(node.name)
            prnt = self.add_item([node.name, b, node.linenum, col], parent)
            self.populate(node.getChildNodes(), prnt)

    def beautify(self, el):
        mu = ('<span size="small"><span%s><b><i>%s</i></b></span>  '
              '<tt><b>%s</b>\n'
              '  %s</tt></span>')
        name = el.name
        typl = el.type[0].lower()
        col = ''
        if self.prop_main_registry.python_browser.use_colors.value():
            if typl == 'f':
                col = ' foreground="#0000c0"'
            else:
                col = ' foreground="#c00000"'
        fl = el.getLine(0).strip().split(' ', 1)[-1].replace(name, '', 1)
        return mu % (col, typl, name, fl)

class RefTree(gtkextra.Tree):
    COLUMNS = [('name', gobject.TYPE_STRING, None, False, None),
               ('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('line', gobject.TYPE_INT, None, False, None),
               ('column', gobject.TYPE_INT, None, False, None)]

    def populate(self, nodes):
        self.clear()
        for node in nodes:
            b = self.beautify(node)
            self.add_item([node.filename, b, node.lineno, node.colno])
        self.update()

    def beautify(self, element):
        rel = ('<span size="small"><span weight="bold">%s</span>'
               ' (L<span foreground="#0000aa" weight="bold">%s</span>,'
               ' C<span foreground="#0000aa" weight="bold">%s</span>)\n'
               '%s</span>')
        dir, name = os.path.split(element.filename)
        disp = rel % (name, element.lineno, element.colno, dir)
        s = '%s:%s' % (element.lineno, element.colno)
        return disp

class RefWin(gtkextra.Transient):

    def populate_widgets(self):
        self.tree = RefTree()
        self.frame.pack_start(self.tree.win)

class Plugin(plugin.Plugin):
    ICON = 'python'
    DICON = 'run', 'Execute Python script'
    NAME = "python_browser"

    def configure(self, reg):
        self.registry = reg.add_group('python_browser',
            'The Python sopurce code browser.')
        self.registry.add('use_colors',
            registry.Boolean,
            1,
            'Whether colors will be used in the definition list')
      

    def populate_widgets(self):

        vp = gtk.VPaned()
        self.add(vp)

        self.defs = DefTree()
        vp.pack1(self.defs.win, resize=True, shrink=True)

        self.refwin = RefWin()
        vp.pack2(self.refwin.win, resize=True, shrink=True)

        self.refs = self.refwin.tree
        
        self.add_button('warning', self.cb_but_pydoc , 'Look up in Pydoc')
        #self.add_button('profile', self.cb_but_profile, 'Run in the Python profiler')
        #self.add_button('debug', self.cb_but_debug, 'Run in the Python debugger')
        self.add_separator()
        self.add_button('undo', self.cb_but_undo, 'Undo last refactoring')
        self.add_button('rename', self.cb_but_rename, 'Rename class or method')
        self.add_button('find', self.cb_but_references, 'List references.')

        #self.menu = gtkextra.PositionPopup('position')

    def connect_widgets(self):
        self.defs.connect_select(self.cb_defs_select)
        self.refs.connect_select(self.cb_refs_select)
        #self.defs.connect_rightclick(self.cb_defs_rclick)
        #self.refs.connect_rightclick(self.cb_refs_rclick)

    def get_references(self, label='References'):
        row, col = self.defs.selected(2), self.defs.selected(3)
        brmc = brm()
        if row and col:
            d = brmc.findReferencesByCoordinates(self.fn, int(row), int(col))
            self.refresh_refs(d, label)
        else:
            self.message('Please select a definition')

    def refresh_defs(self, fn):
        self.fn = fn
        f = open(fn)
        root = fastparser.fastparser(f.read())
        f.close()
        self.defs.clear()
        self.defs.populate(root.getChildNodes())
   
    def refresh_refs(self, refs, label="References"):
        refs = [i for i in refs]
        self.refs.populate(refs)
        s = '%s: %s' % (label, len(refs))
        self.refwin.show(s)

    def execute(self):
        py = self.prop_main_registry.commands.python.value()
        dirn = os.path.split(self.fn)[0]
        self.do_action('newterminal', '%s %s' % (py, self.fn), directory=dirn)

    def cb_alternative(self):
        self.execute()
        
    def cb_but_pydoc(self, *args):
        def ans(text):
            self.evt_doc(text)
        self.question('Search Pydoc for:', ans)

    def cb_defs_select(self, tv):
        self.do_edit('gotoline', self.defs.selected(2))

    def cb_refs_select(self, tv):
        fn, line, col = [self.refs.selected(i) for i in [0, 2, 3]]
        if fn != self.fn:
            self.do_edit('openfile', fn)
        self.do_edit('gotoline', line)

    def cb_defs_rclick(self, ite, time):
        line = self.defs.get(ite, 2)
        self.menu.popup(self.fn, line, time)

    def cb_refs_rclick(self, ite, time):
        line = self.refs.get(ite, 2)
        self.menu.popup(self.fn, line, time)

    def cb_but_rename(self, *a):
        self.get_references(label='Renames')
        brmc = brm()
        def rename(name):
            row, col = self.tree.get_selected_id()
            brmc.renameByCoordinates(self.fn, int(row), int(col), name)
            brmc.save()
            self.refresh(self.fn)
        self.question('Name to rename to?', rename)

    def cb_but_references(self, *a):
        self.get_references()

    def cb_but_undo(self, *args):
        brmc = brm()
        brmc.undo()
        brmc.save()
        self.refresh(self.fn)

    def evt_bufferchange(self, nr, name):
        self.fn = name
        if name.endswith('py') and os.path.exists(name):
            self.refresh_defs(name)
        else:
            self.defs.model.clear()

    def evt_bufferexecute(self, *args):
        self.execute()

    def evt_started(self, *args):
        brm()
        self.refwin.hide()

    def evt_doc(self, text):
        pydoc = self.prop_main_registry.commands.pydoc.value()
        self.do_action('newterminal', '%s %s' % (pydoc, text))




