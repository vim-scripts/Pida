# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 449 2005-07-24 01:11:29Z aafshar $
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

''' The Pida profiler plugin '''

#system imports
import os
import cgi
import profile
import cPickle as pickle

# GTK imports
import gtk
import gobject

# Pida imports
#import tree
import pida.base as base
import pida.plugin as plugin
import pida.gtkextra as gtkextra
import pida.gobjectreactor as gobjectreactor

def script_directory():
    def f(): pass
    d, f = os.path.split(f.func_code.co_filename)
    return d

SCRIPT_DIR = script_directory()


class DetailsWindow(gtk.Window):

    def __init__(self, treemodel):
        gtk.Window.__init__(self)
        self.set_title('PIDA Profiler Detailed View')
        self.set_size_request(640, 400)
        self.treeview = gtk.TreeView(treemodel)
        self.treeview.set_headers_clickable(True)
        self.treeview.set_rules_hint(True)
        sw = gtk.ScrolledWindow()
        sw.add(self.treeview)
        self.add(sw)
        for i, col in enumerate(PstatsTree.COLUMNS[1:]):
            renderer = gtk.CellRendererText()
            renderer.set_property('scale', 0.8)
            column = gtk.TreeViewColumn(col[0], renderer, text=i+1)
            
            #column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
            column.set_expand(False)
            column.set_clickable(True)
            column.set_sort_column_id(i+1)
            column.set_resizable(True)
            #column.connect('clicked', self.cb_col_clicked)
            self.treeview.append_column(column)

    def cb_col_clicked(self, col):
        pass


class PstatsTree(gtkextra.Tree):
    COLUMNS = [('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('filename', gobject.TYPE_STRING, gtk.CellRendererText, False,
                'text'),
               ('lineno', gobject.TYPE_INT, gtk.CellRendererText, False,
                'text'),
               ('function', gobject.TYPE_STRING, gtk.CellRendererText, False,
                'text'),
               ('number of calls', gobject.TYPE_INT, None, False, None),
               ('total time', gobject.TYPE_FLOAT, None, False, None),
               ('total per call', gobject.TYPE_FLOAT, None, False, None),
               ('cumulative time', gobject.TYPE_FLOAT, None, False, None),
               ('cumulative per call', gobject.TYPE_FLOAT, None, False, None)]
                

class Plugin(plugin.Plugin):
    NAME = 'python_profiler'
    DICON = 'profile', 'Profile the current buffer.'
    ICON = 'profile'
    
    def populate_widgets(self):

        sb = gtk.HBox()
        self.add(sb, expand=False)

        self.sortbox = gtk.combo_box_new_text()
        self.sortbox.connect('changed', self.cb_sort_changed)
        sb.pack_start(self.sortbox)

        self.sortascending = gtk.CheckButton(label="asc")
        self.sortascending.set_active(True)
        self.sortascending.connect('toggled', self.cb_sort_changed)
        
        sb.pack_start(self.sortascending)

        self.pstats = PstatsTree()
        self.add(self.pstats.win)

        for col in self.pstats.COLUMNS[1:]:
            self.sortbox.append_text(col[0])
        self.sortbox.set_active(2)

        self.add_button('fullscreen', self.cb_details,
            'Open results in a separate window.')

        self.profiler = Profiler()
        self.fn = None
        self.readbuf = ''

    def cb_details(self, *args):
        dw = DetailsWindow(self.pstats.model)
        dw.show_all()

    def cb_sort_changed(self, *args):
        order = self.sortbox.get_active() + 1
        direction = gtk.SORT_DESCENDING
        if self.sortascending.get_active():
            direction = gtk.SORT_ASCENDING
        self.pstats.model.set_sort_column_id(order, direction)

    def cb_alternative(self, *args):
        #if self.fn and self.fn.endswith('.py'):
        self.profiler.run(self.fn, self.cb_stats)
            
    def cb_stats(self, statsdict):
        self.pstats.clear()
        for k in statsdict:
            fn, line, func = k
            ncalls, pcalls, tottime, cumtime, callers = statsdict[k]
            d, f = os.path.split(fn)
            totper = cumper = 0
            if ncalls > 0:
                totper = tottime / ncalls
                cumper = cumtime / ncalls
            
            mu = self.markup(f, d, line, func,
                                ncalls, tottime, totper, cumtime, cumper)
            self.pstats.add_item([mu, fn, line, func,
                                ncalls, tottime, totper, cumtime, cumper])

    def markup(self, fn, dn, line, func, ncalls, tott, totper, cumt, cumper):
        MU = ('<span size="small"><b>%s()</b> %s ('
              '<span foreground="#0000c0">%s</span>) %s\n'
              'N:<b>%s</b> T:<b>%s</b>/<b>%s</b> '
              'C:<b>%s</b>/<b>%s</b></span>')
        return MU % (cgi.escape(func), cgi.escape(fn),
                     line, dn, ncalls, tott, totper, cumt, cumper)


    def evt_bufferchange(self, nr, name):
        self.fn = name


class Profiler(base.pidaobject):

    def do_init(self):
        sockdir = self.prop_main_registry.directories.socket.value()
        self.parentsock = os.path.join(sockdir, 'profiler_parent')
        self.childsock = os.path.join(sockdir, 'profiler_child')
        self.reactor = gobjectreactor.Reactor(self, self.parentsock,
                                              self.childsock)
        #self.ipc = gtkextra.IPWindow(self)
        self.r_cb_stats = None

    def run(self, filename, statscb):
        self.r_cb_stats = statscb
        self.reactor.start()
        profilerfn = os.path.join(SCRIPT_DIR, 'profiler.py')
        #xid = '%s' % self.ipc.get_lid()
        py = self.prop_main_registry.commands.python.value()
        pid = os.fork()
        if pid == 0:
            os.execvp(py, ['python', profilerfn, filename, self.parentsock,
                            self.childsock])
        else:
            self.pid = pid
        print 'run'

    def do_stats(self, outf):
        f = open(outf, 'r')
        stats = pickle.load(f)
        f.close()
        os.remove(outf)
        if self.r_cb_stats:
            self.r_cb_stats(stats)



