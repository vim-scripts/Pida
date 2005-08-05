# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 429 2005-07-21 20:55:07Z aafshar $


import pida.plugin as plugin
import gtk
import os
import pickle
#import tree
import gobject
import tempfile
import pida.base as base
import pida.gtkextra as gtkextra
import pida.gobjectreactor as gobjectreactor
import linecache
import marshal
import cStringIO

def script_directory():
    def f(): pass
    d, f = os.path.split(f.func_code.co_filename)
    return d

SCRIPT_DIR = script_directory()

class StackTree(gtkextra.Tree):
    COLUMNS = [('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('frame', gobject.TYPE_PYOBJECT, None, False, None)]

    #def init(self):
    #    self.title = gtk.Label()
    #    self.toolbar.pack_start(self.title)
    #    self.refresh_label()
    #def l_cb_selected(self, tv):
    #    #self.fv.refresh_label(self.selected(1))
    #def refresh_label(self):
    #    self.title.set_markup('Stack')


    def populate(self, stack, curindex):
        self.clear()
        last = None
        for fr in stack:
            if not fr.filename.count('bdb.py') and fr.filename != '<string>':
                last = self.add_item([fr.markup(), fr])
        if last:
            path = self.model.get_path(last)
            self.view.set_cursor(path)

class BreakTree(gtkextra.Tree):
    COLUMNS = [('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('filename', gobject.TYPE_STRING, None, False, None),
               ('line', gobject.TYPE_STRING, None, False, None)]

    #def init(self):
    #    self.title = gtk.Label()
    #    self.toolbar.pack_start(self.title)
    #    self.refresh_label()

    def refresh_label(self):
        self.title.set_markup('Breakpoints')

    def add(self, filename, line):
        mu = self.markup(filename, line)
        self.add_item([mu, filename, line])

    def get_list(self):
        for row in self.model:
            # not allowed to slice row sequences
            yield [row[1], row[2]]

    def markup(self, filename, line):
        dn, fn = os.path.split(filename)
        MU = ('<span size="small"><b>%s</b> '
              '(<span foreground="#0000c0">%s</span>)\n'
              '%s</span>')
        return MU % (fn, line, dn)

def bframe(frame):
    c = frame.f_code
    return '%s %s %s %s %s' % (c.co_name,
        c.co_argcount, c.co_names, c.co_filename, c.co_firstlineno)

class VarTree(gtkextra.Tree):
    COLUMNS = [('display', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('dispval', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('name', gobject.TYPE_STRING, None, False, None),
               ('value', gobject.TYPE_STRING, None, False, None)]
    
    VAR_COLOR = '#c00000'
    
    def populate(self, varlist):
        self.clear()
        varlist.sort()
        for n, v in varlist:
            self.add_item(self.markup(n, v) + [n, v])

    def markup(self, name, value):
        MUN = '<span size="small"><b>%s</b></span>'
        MUV = '<span size="small" foreground="%s">%%s</span>' % self.VAR_COLOR
        return [(MUN % name), (MUV % value)]

class LocalsTree(VarTree):
    VAR_COLOR = '#0000c0'

from cgi import escape

class PidaFrame(object):
    def __init__(self, fn, lineno, name, args, ret, line, locs, globs=None):
        self.filename = fn
        self.lineno = lineno
        self.name = name
        self.args = args
        self.line = line
        self.ret = ret
        self.locs = locs
        self.globs = globs

    def markup(self):
        t = ('<span size="small">%s\n'
            '%s (%s)\n<b>%s(</b>%s<b>)</b> &gt; %s\n<tt>%s</tt></span>')
        dirn, filen = os.path.split(self.filename)
        
        return t % tuple([escape('%s' % s) for s in [dirn, filen, self.lineno,
                                        self.name, ', '.join(self.args),
                                        self.ret, self.line]])

class FrameViewer(gtk.Label):
    MU = ('<span size="small">'
               '<b>%s</b>'
               ' (<span color="#0000c0">%s</span>)\n'
               '%s\n<tt>%s</tt></span>')

    def refresh_label(self, fr):
        return
        dn, fn = os.path.split(fr['filename'])
        mu = self.MU % (fn, fr['line'], dn, fr['so'])
        self.set_markup(mu)

import vte

class DebugTerminal(base.pidaobject, vte.Terminal):

    def do_init(self):
        self.pid = None
        vte.Terminal.__init__(self)
        font = self.prop_main_registry.terminal.font.value()
        self.set_font_from_string(font)
        self.set_size_request(-1, 32)

    def kill(self):
        if self.pid:
            try:
                os.kill(self.pid, 15)
            except OSError:
                try:
                    os.kill(self.pid, 15)
                except OSError:
                    pass

    def start(self, fn, parentsock, childsock):
        self.kill()
        sn = os.path.join(SCRIPT_DIR, 'debugger.py')
        c = self.prop_main_registry.commands.python.value()
        args = ['python', sn, fn, parentsock, childsock]
        self.pid = self.fork_command(c, args)
        self.grab_focus()
        return self.pid

class DumpWindow(gtkextra.Transient):

    def populate_widgets(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.dumpbuf = gtk.TextBuffer()
        self.dumptag = self.dumpbuf.create_tag(scale=0.8)
        self.dumptext = gtk.TextView(self.dumpbuf)
        self.dumptext.set_wrap_mode(gtk.WRAP_CHAR)
        self.dumptext.set_size_request(-1, 75)
        self.dumptext.set_editable(False)
        sw.add(self.dumptext)
        self.frame.pack_start(sw)

    def set_text(self, s):
        self.dumpbuf.set_text(s)
        start = self.dumpbuf.get_start_iter()
        end = self.dumpbuf.get_end_iter()
        self.dumpbuf.apply_tag(self.dumptag, start, end)
        

class Plugin(plugin.Plugin):
    NAME = 'python_debugger'
    ICON = 'debug'
    DICON = 'debug', 'Load current buffer into debugger.'

    def create_reactor(self):
        sockdir = self.prop_main_registry.directories.socket.value()
        self.parentsock = os.path.join(sockdir, 'profiler_parent')
        self.childsock = os.path.join(sockdir, 'profiler_child')
        self.reactor = gobjectreactor.Reactor(self, self.parentsock,
                                              self.childsock)

    def populate_widgets(self):
        self._dbg = None
        
        self.create_reactor()
        #self.ipc = gtkextra.IPWindow(self)
        #self.add_button('debug', self.cb_but_debug, 'start')
        self.add_button('stop', self.cb_but_stop, 'Stop debugging.')
        self.add_button('step', self.cb_step, 'step')
        self.add_button('jump', self.cb_next, 'next')
        self.add_button('continue', self.cb_continue, 'continue')
        self.add_button('list', self.cb_but_list, 'Show source code context.')

        vp = gtk.VPaned()
        self.add(vp)
        
        tb = gtk.VBox()
        vp.pack1(tb)


        self.stack = StackTree()
        tb.pack_start(self.stack.win)
        self.stack.connect_select(self.cb_stack_select)
        self.stack.connect_activate(self.cb_stack_activate)
        self.stack.connect_rightclick(self.cb_stack_rclick)


        nb = gtk.Notebook()
        vp.pack2(nb)

        brlb = gtk.Label()
        brlb.set_markup('<span size="small">Breaks</span>')
        self.breaks = BreakTree()
        self.breaks.connect_rightclick(self.cb_breaks_rclick)
        nb.append_page(self.breaks.win, tab_label=brlb)

        loclb = gtk.Label()
        loclb.set_markup('<span size="small">Locals</span>')
        self.locs = LocalsTree()
        self.locs.connect_activate(self.cb_locs_activate)
        nb.append_page(self.locs.win, tab_label=loclb)

        gllb = gtk.Label()
        gllb.set_markup('<span size="small">Globals</span>')
        self.globs = VarTree()
        self.globs.connect_activate(self.cb_globs_activate)
        nb.append_page(self.globs.win, tab_label=gllb)

        self.dumpwin = DumpWindow()
        self.add(self.dumpwin.win, expand=False)

        self.term = DebugTerminal()
        self.add(self.term, expand=False)

        self.curindex = 0
        self.menu = gtkextra.PositionPopup('position')
        self.lfn = tempfile.mktemp('.py', 'pidatmp')
        self.debugger_loaded = False

    def do_list(self, s):
        f = open(self.lfn, 'w')
        f.write(s)
        f.close()
        self.do_edit('preview', self.lfn)

    def do_eval(self, s, *args):
        com, val = s.split('\n', 1)
        self.dumpwin.set_text(val)
        self.dumpwin.show('<span size="small">%s</span>' % com)

    def do_started(self, *args):
        self.load_breakpoints()

    def do_frame(self, fs):
        self.curindex = fs.pop()
        
    def do_stack(self, stacks):
        stack = pickle.loads(stacks)
        self.stack.populate([PidaFrame(*fr) for fr in stack], -1)
        curframe = PidaFrame(*stack[-1])
        self.do_evt('debuggerframe', curframe)
        

    def send(self, command):
        if self.term.pid:
            self.term.feed_child('%s\n' % command)

    def send_breakpoint(self, fn, line):
        self.send('break %s:%s' % (fn, line))

    def send_breakpoint_clear(self, fn, line):
        self.send('clear %s:%s' % (fn, line))

    def load_breakpoints(self):
        for bp in self.breaks.get_list():
            self.send_breakpoint(*bp)

    def load(self):
        self.reactor.start()
        pid = self.term.start(self.fn, self.parentsock, self.childsock)
        self.debugger_loaded = True
        
    def evt_debuggerload(self):
        self.load()
        
    def evt_step(self):
        self.send('step')
        
    def evt_next(self):
        self.send('next')
        
    def evt_continue(self):
        self.send('continue')
        
    def cb_breaks_rclick(self, ite, time):
        fn = self.breaks.get(ite, 1)
        line = self.breaks.get(ite, 2)
        self.menu.popup(fn, line, time)

    def cb_stack_rclick(self, ite, time):
        frame = self.stack.get(ite, 1)
        fn = frame.filename
        line = frame.lineno
        self.menu.popup(fn, line, time)

    def cb_but_debug(self, *args):
        self.load()

    cb_alternative = cb_but_debug

    def cb_but_stop(self, *args):
        self.send('quit')
        self.term.kill()

    def cb_but_list(self, *args):
        self.goto_stack()
        
    def goto_stack(self):
        frame = self.stack.selected(1)
        fn = frame.filename
        line = frame.lineno
        if fn != self.fn:
            self.do_edit('openfile', fn)
        self.do_edit('gotoline', line)
        #self.send('list')

    def set_breakpoint(self, fn, line):
        exist = []
        def exists(model, path, ite, exist):
            if self.breaks.get(ite, 1) == fn:
                if self.breaks.get(ite, 2) == line:
                    exist.append(True)
        self.breaks.model.foreach(exists, exist)
        if not exist:
            self.breaks.add(fn, line)
            if self.debugger_loaded:
                self.send_breakpoint(fn, line)

    def clear_breakpoint(self, fn, line):
        def remove(model, path, ite):
            if self.breaks.get(ite, 1) == fn:
                if self.breaks.get(ite, 2) == line:
                    self.breaks.model.remove(ite)
        self.breaks.model.foreach(remove)
        if self.debugger_loaded:
            self.send_breakpoint_clear(fn, line)

    def cb_step(self, *args):
        self.send('step')

    def cb_next(self, *args):
        self.send('next')

    def cb_continue(self, *args):
        self.send('continue')

    def cb_stack_select(self, ite):
        frame = self.stack.selected(1)
        self.locs.populate(frame.locs)
        self.globs.populate(frame.globs)

    def cb_stack_activate(self, tree, path, col):
        self.goto_stack()

    def cb_locs_activate(self, tree, path, col):
        v = self.locs.selected(2)
        self.send(v)

    def cb_globs_activate(self, tree, path, col):
        v = self.globs.selected(2)
        self.send(v)

    def evt_bufferchange(self, nr, name):
        self.fn = name

    def evt_die(self):
        self.term.kill()

    def evt_breakpointset(self, line, fn=None):
        if not fn:
            fn = self.fn
        if fn:
            self.set_breakpoint(fn, line)

    def evt_breakpointclear(self, line, fn=None):
        line = '%s' % line
        if not fn:
            fn = self.fn
        if fn:
            self.clear_breakpoint(fn, line)

    def evt_started(self, *args):
        self.dumpwin.hide()


