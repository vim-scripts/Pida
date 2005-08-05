# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 481 2005-08-02 11:54:55Z aafshar $
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

# System imports
import os
import re

# GTK imports
import gtk

# vte terminal emulator widget
try:
    import vte
except ImportError:
    class Dummy(object):
        Terminal = object
        bad = True
    vte = Dummy

# Pida imports
import pida.base as base
import pida.plugin as plugin
import pida.gtkextra as gtkextra
import pida.configuration.registry as registry

class Terminal(base.pidaobject, vte.Terminal):
    """ A terminal emulator widget that uses global config information. """
    def do_init(self):
        vte.Terminal.__init__(self)
        ## set config stuff
        # transparency
        trans = self.prop_main_registry.terminal.enable_transparency.value()
        if trans:
            self.set_background_transparent(trans)
        # colors
        # get the colour map
        cmap = self.get_colormap()
        # bg
        c = self.prop_main_registry.terminal.background_color.value()
        bgcol = cmap.alloc_color(c)
        # fg
        c = self.prop_main_registry.terminal.foreground_color.value()
        fgcol = cmap.alloc_color(c)
        # set to the new values
        self.set_colors(fgcol, bgcol, [])
        #font
        font = self.prop_main_registry.terminal.font.value()
        self.set_font_from_string(font)
        # set the default size really small
        self.set_size(60, 10)
        self.set_size_request(-1, 50)

    def feed(self, text, color=None):
        """ Feed text to the terminal, optionally coloured."""
        if color:
            # construct the ansi escape sequence
            text = '\x1b[%sm%s\x1b[0m' % (color, text)
        # call the superclass method
        vte.Terminal.feed(self, text)

class PidaTerminal(base.pidaobject, gtk.VBox):
    """ A terminal emulator widget aware of the notebook it resides in. """
    def do_init(self, notebook, icon, immortal=False):
        # the parent notebook
        self.notebook = notebook
        # generate widgets
        gtk.VBox.__init__(self)
        self.show()
        # terminal widget
        self.term = Terminal()
        self.pack_start(self.term)
        self.term.show()
        # connect the terminal widget's signals
        self.term.connect('button_press_event', self.cb_button)
        self.term.connect('child-exited', self.cb_exited)
        # tab label
        self.label = Tablabel(icon)
        # can we be killed?
        self.immortal=immortal
        # a handler for right click matching
        # may be removed
        self.match = MatchHandler()
        # the PID of the child process
        self.pid = -1

    def run_command(self, command, args=[], **kw):
        """ Fork a system command in the terminal """
        self.term.feed('Executing ')
        self.term.feed(command, '34;1')
        self.term.feed(' %s\r\n' % args)
        self.pid = self.term.fork_command(command, args, **kw)
        # give the terminal focus
        self.term.grab_focus()

    def popup(self, word):
        """ Popup the terminal context menu """
        menu = TerminalMenu(self.pida)
        menu.set_title(word)

    def kill(self):
        """ Attempt to forcibly teminate the child process, if running """
        if self.pid > 0:
            try:
                os.kill(self.pid, 15)
            except OSError:
                pass #"already terminated"

    def remove(self):
        """ Remove own page from parent notebook """
        index = self.notebook.page_num(self)
        if self.immortal:
            return False
        else:
            self.notebook.remove_page(index)
            return True

    def right_press(self, x, y):
        """ Right click handler """
        word = self.word_from_coord(x, y)
        self.match.match(word)

    def word_from_coord(self, x, y):
        """ Retrieve the word in the terminal at cursor coordinates """
        def isin(term, cx, cy, *args):
            if cy == y:
                return True
            else:
                return False
        line = self.term.get_text_range(y, 0, y, -1, isin)
        if x <= len(line):
            p1, p2 = line[:x], line[x:]
            p1 = p1.split()[-1]
            p2 = p2.split()[0]
            word = ''.join([p1, p2])
            return word

            
    def char_from_coord(self, cx, cy):
        """ Character coordinates for cursor coordinates. """
        h = self.term.get_char_height()
        w = self.term.get_char_width()
        ya = self.term.get_adjustment().value
        x = int(cx/w)
        y = int((cy)/h + ya)
        return x, y

    def cb_button(self, terminal, event):
        """ Mouse button event handler. """
        if event.button == 3:
            if event.type == gtk.gdk.BUTTON_PRESS:
                cc = self.char_from_coord(event.x, event.y)
                self.right_press(*cc)

    def cb_exited(self, *a):
        """ Child exited event handler. """
        self.pid = -1
        self.term.feed('\r\nchild exited ', '1;34')
        self.term.feed('press any key to close')
        self.term.connect('commit', self.cb_anykey)
    
    def cb_anykey(self, *a):
        """ Any key event handler. """
        self.remove()

class Tablabel(base.pidaobject, gtk.EventBox):
    """ A label for a notebook tab. """
    def do_init(self, stockid):
        # Construct widgets
        gtk.EventBox.__init__(self)
        self.set_visible_window(True)
        # Get the requested icon
        self.image = self.do_get_image(stockid)
        self.add(self.image)
        # Different styles for highligting labels
        self.hst = self.style.copy()
        self.dst = self.style
        col = self.get_colormap().alloc_color('#FF8080')
        for i in xrange(5):
            self.hst.bg[i] = col
        self.show_all()

    def read(self):
        """ Called to unhighlight the tab label """
        self.set_style(self.dst)
   
    def unread(self):
        """ Highlight the tab label """
        self.set_style(self.hst)

class PidaBrowser(gtk.VBox):
    def __init__(self, notebook, icon, immortal=False):
        self.cb = cb
        # the parent notebook
        self.notebook = notebook
        # generate widgets
        gtk.VBox.__init__(self)
        # terminal widget
        # tab label
        self.label = Tablabel(self.cb, icon)
        # can we be killed?
        self.immortal=immortal
        # the PID of the child process
        self.pid = -1

        self.toolbar = gtkextra.Toolbar(self.cb)
        
        self.pack_start(self.toolbar.win, expand=False)

        self.back_but = self.toolbar.add_button('left', self.cb_back, 'Go back')
        self.next_but = self.toolbar.add_button('right', self.cb_forw, 'Go Forwards')
        self.toolbar.add_button('close', self.cb_stop, 'Stop loading')
        self.toolbar.add_button('refresh', self.cb_reload, 'Reload Page')

        self.urlentry = gtk.Entry()
        self.urlentry.connect('activate', self.cb_urlentered)
        self.toolbar.win.pack_start(self.urlentry)

        self.progresslabel = gtk.Label()
        self.toolbar.win.pack_start(self.progresslabel, expand=False)

        self.next_but.set_sensitive(False)
        self.back_but.set_sensitive(False)

        self.socket = gtk.Socket()
        self.pack_start(self.socket)
        self.socket.realize()


    def cb_moz_progress(self, moz, cur, max):
        self.progresslabel.set_markup('<span size="x-small">%s</span>' % cur)

    def cb_moz_location(self, moz):
        self.back_but.set_sensitive(self.moz.can_go_back())
        self.next_but.set_sensitive(self.moz.can_go_forward())
        self.urlentry.set_text(self.moz.get_location())

    def cb_urlentered(self, entry):
        url = self.urlentry.get_text()
        self.gourl(url)

    def cb_back(self, button):
        self.moz.go_back()

    def cb_forw(self, button):
        self.moz.go_forward()

    def cb_reload(self, button):
        self.moz.reload(0)

    def cb_stop(self, button):
        self.moz.stop_load()

    def gourl(self, url):
        if not os.fork():
            os.execvp('dillo', ['dillo', '-f', '-x', '%s' % self.socket.get_id()])

    def kill(self):
        self.remove()

    def remove(self):
        """ Remove own page from parent notebook """
        index = self.notebook.page_num(self)
        self.notebook.remove_page(index)
        
class Plugin(plugin.Plugin):
    """ The terminal emulator plugin """
    NAME = "Shell"
    DETACHABLE = True

    def init(self):
        pass

    def configure(self, reg):
        ### Terminal emulator options
        
        self.registry = reg.add_group('terminal',
            'Options for the built in terminal emulator.')

        self.registry.add('internal',
            registry.Boolean,
            True,
            'Determines whether Pida will use its builtin terminal emulator '
            '(otherwise will use Xterm).')
        
        self.registry.add('font',
                       registry.Font,
                       'Monospace 10',
                       'The font for newly started terminals.')

        self.registry.add('enable_transparency',
                       registry.Boolean,
                       0,
                       'Determines whether terminals will appear transparent')
                       
        self.registry.add('background_color',
                registry.Color,
                '#000000',
                'The background colour for terminals')

        self.registry.add('foreground_color',
                registry.Color,
                '#d0d0d0',
                'The foreground colour for terminals')
        
        self.registry.add('on_top',
                registry.Boolean,
                False,
                'Is the detached window on top of main PIDA window? (Transient'
                ' window)')
    
    def populate_widgets(self):
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.notebook.set_scrollable(True)
        self.notebook.set_property('show-border', False)
        self.notebook.set_property('tab-border', 2)
        self.notebook.set_property('enable-popup', True)
        self.add(self.notebook)
        self.add_separator()
        self.add_button('python', self.cb_python,
                        'Open a python shell')
        self.add_button('internet', self.cb_new_browser,
                        'Open a new browser')
        self.add_button('terminal', self.cb_new,
                        'Open a new shell')
        self.add_button('close', self.cb_close,
                        'Close current tab.')
       
        self.panes = {}
        self.toolbar_popup.add_separator()
        self.toolbar_popup.add_item('configure',
                            'Configure this shortcut bar',
                            self.cb_conf_clicked, [])

    def cb_python(self, *args):
        self.do_action('newterminal', 'python')

    def cb_conf_clicked(self, *args):
        self.cb.action_showshortcuts()

    def connect_widgets(self):
        self.notebook.connect('switch-page', self.cb_switch)

    def add_terminal(self, ttype, icon, immortal=False):
        child = ttype(self.notebook, icon, immortal)
        child.show_all()
        self.notebook.append_page(child, tab_label=child.label)
        for i in range(self.notebook.get_n_pages()):
            self.notebook.set_current_page(i)
        #self.notebook.show_all()
        return child

    def remove_terminal(self, index):
        child = self.notebook.get_nth_page(index)
        if child:
            child.kill()
            removed = child.remove()
        return True
        

    def new_browser(self, url):
        if not url:
            url = 'http://www.google.com/'
        args = self.prop_main_registry.commands.browser.value().split(' ', 1)
        com = args.pop(0)
        pid = os.fork()
        if not pid:
            os.execlp(com, com,  *(args+[url]))
        #child = self.add_terminal(PidaBrowser, 'internet', False)
        #child.gourl(url)
        #child.run_command(command, args, **kw)
        #if self.detach_window:
        #    self.detach_window.present()
        #return child

    def new_command(self, command, args, icon, **kw):
        if command == 'browseurl':
            url = None
            if len(args) > 1:
                url = args.pop()
            return self.new_browser(url)
        child = self.add_terminal(PidaTerminal, icon, False)
        child.run_command(command, args, **kw)
        if self.detach_window:
            self.detach_window.present()
        return child

    def evt_terminal(self, commandline, **kw):
        if not hasattr(vte, 'bad') and self.registry.internal.value():
            self.termmap_internal(commandline, **kw)
        else:
            self.termmap_xterm(commandline, **kw)

    def evt_killterminal(self):
        self.cb_close()

    def evt_shortcutschanged(self):
        self.ctxbar.refresh()
        self.ctxbar.show()

    def cb_new(self, *args):
        shell = self.prop_main_registry.commands.shell.value()
        self.do_action('newterminal', 'bash', icon='terminal')

    def cb_new_browser(self, *args):
        self.new_browser(None)

    def cb_close(self, *args):
        if not self.remove_terminal(self.notebook.get_current_page()):
            self.error('cannot remove log window')

    def cb_changed(self, terminal):
        cpage = self.notebook.get_nth_page(self.notebook.get_current_page())
        if terminal != cpage:
            terminal.label.unread()

    def cb_switch(self, notebook, p, id, *args):
        self.notebook.get_nth_page(id).label.read()

    def cb_browser(self, *args):
        self.new_browser('http://www.google.com/')

    def termmap_internal(self, commandline, **kw):
        icon = 'terminal'
        if 'icon' in kw:
            icon = kw['icon']
            del kw['icon']
        child = PidaTerminal(self.notebook, icon)
        args = commandline.split()
        command = args.pop(0)
        args.insert(0, 'PIDA')
        child.run_command(command, args, **kw)
        if self.detach_window:
            self.detach_window.present()
        self.notebook.append_page(child, tab_label=child.label)
        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        child.show_all()
        return child

    def termmap_xterm(self, commandline, **kw):
        xterm = 'xterm'
        self.termmap_external(xterm, commandline, **kw)

    def termmap_external(self, termpath, commandline, **kw):
        commandargs = [termpath, '-hold', '-e', commandline]
        self.do_action('fork', commandargs)

# will vanish, superceded by plugin.ContextMenu
class TerminalMenu(base.pidaobject, gtk.Menu):
    def do_init(self):
        gtk.Menu.__init__(self)

    def add_item(self, name, callback, *args):
        item = gtk.MenuItem(label=name)
        item.connect('activate', callback, *args)
        item.show()
        self.append(item)

    def set_title(self, title):
        item = gtk.MenuItem(label=title)
        item.show()
        self.prepend(item)        

class Match(base.pidaobject):
    RE = re.compile('.+')
    
    def do_init(self):
        self.menu = TerminalMenu()
        self.generate_menu()

    def check(self, word):
        try:
            return self.RE.search(word)
        except TypeError:
            return None

    def popup(self, word):
        self.word = word
        self.menu.popup(None, None, None, 3, 0)

    def add_match_command(self, name, cmd, args):
        self.menu.add_item(name, self.cb_newcommand, cmd, args)

    def cb_newcommand(self, menu, cmd, args):
        args = list(args)
        args.append(self.word)
        self.do_action('newterminal', ' '.join([cmd] + args))

class DefaultMatch(Match):
    def generate_menu(self):
        self.add_match_command('dict',
                                '/usr/bin/dict', [])

class URLMatch(Match):
    RE = re.compile('http')
    def generate_menu(self):
        obrowser = self.prop_main_registry.commands.browser.value()
        self.add_match_command('external',
                                obrowser, [])

class NumberMatch(Match):
    RE = re.compile('[0-9].+')
    def generate_menu(self):
        self.menu.add_item('jump to', self.cb_jump)
        self.menu.add_item('kill 15', self.cb_kill)
    
    def cb_jump(self, *args):
        self.do_edit('gotoline', int(self.word.strip(',.:')))
        
    def cb_kill(self, *args):
        os.kill(int(self.word), 15)

class MatchHandler(base.pidaobject):
    def do_init(self):
        self.matches = [NumberMatch(),
                        URLMatch(),
                        DefaultMatch()]

    def match(self, word):
        for m in self.matches:
            if m.check(word):
                m.popup(word)
                break
