# Copyright (C) 2005 by Async Open Source and Sicem S.L.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import gettext
import linecache
import os
import sys
import traceback

import pango
import gtk

_ = gettext.gettext

class DebugWindow(gtk.Dialog):

    application = None
    
    def __init__(self, parent=None):
        gtk.Dialog.__init__(self, 'An Error Occurred', parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_NO_SEPARATOR)

        self._build_ui()
        #self.send = self._create_button(gtk.STOCK_NETWORK, _('_Report bug ...'))
        #self.send.connect('clicked', self._on_send__clicked)
        #self.action_area.pack_end(self.send)

        
        quit = self._create_button(gtk.STOCK_OK, _('_Continue'))
        self.add_action_widget(quit, gtk.RESPONSE_ACCEPT)
        
        self._pwd = os.getcwd()

    def _create_button(self, stock, text):
        b = gtk.Button()
        #a = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        h = gtk.HBox()
        #a.add(h)
        i = gtk.Image()
        i.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        l = gtk.Label(text)
        if '_' in text:
            l.set_use_underline(True)

        h.pack_start(i)
        h.pack_start(l)
        b.add(h)
        b.show_all()
        return b
        
    def _build_ui(self):
        # 416 = 600 / sqrt(2) = golden number
        self.set_default_size(600, 416) 
        self.set_border_width(12)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox, False, False)
        self.vbox.set_spacing(6)
        lbl = gtk.Label('<b>Exception type:</b>')
        lbl.set_use_markup(True)
        hbox.pack_start(lbl, False, False, 6)
        lbl.show()
        self._info_label = gtk.Label()
        hbox.pack_start(self._info_label, False, False)
        self._info_label.show()
        hbox.show()

        self.notebook = gtk.Notebook()
        self.vbox.pack_start(self.notebook)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.show()
        
        self._buffer = gtk.TextBuffer()
        self._buffer.create_tag('filename', style=pango.STYLE_ITALIC, foreground='gray20')
        self._buffer.create_tag('name', foreground='#000055')
        self._buffer.create_tag('lineno', weight=pango.WEIGHT_BOLD)
        self._buffer.create_tag('exc', foreground='#880000', weight=pango.WEIGHT_BOLD)
        
        self._textview = gtk.TextView(self._buffer)
        self._textview.set_editable(False)
        self._textview.set_cursor_visible(False)
        sw.add(self._textview)
        self._textview.show()
        
        self.notebook.append_page(sw, tab_label=gtk.Label("Exception"))
        

        lsw = gtk.ScrolledWindow()
        lsw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        lsw.set_shadow_type(gtk.SHADOW_IN)
        self._lbuf = gtk.TextBuffer()
        self._lview = gtk.TextView(self._lbuf)
        lsw.add(self._lview)
        self.notebook.append_page(lsw, tab_label=gtk.Label("Log"))

        isw = gtk.ScrolledWindow()
        isw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        isw.set_shadow_type(gtk.SHADOW_IN)
        self._ibuf = gtk.TextBuffer()
        self._iview = gtk.TextView(self._ibuf)
        
        isw.add(self._iview)
        self.notebook.append_page(isw, tab_label=gtk.Label("Stdio"))
        
        self.notebook.show_all()

    def show_exception(self, exctype, value, tb):
        self._info_label.set_text(str(exctype))
        self.print_tb(tb)
        lines = traceback.format_exception_only(exctype, value)

        msg = traceback.format_exception_only(exctype, value)[0]
        result = msg.split(' ', 1)
        if len(result) == 1:
            msg = result[0]
            arguments = ''
        else:
            msg, arguments = result
        self._insert(msg, 'exc')
        self._insert(' ' + arguments)

        self.show_log()

    def show_log(self):
        logfn = self.application.registry.files.log.value()
        iofn = '%s.io' % logfn
        lf = open(logfn, 'r')
        self._lbuf.set_text(lf.read())
        lf.close()
        of = open(iofn, 'r')
        self._ibuf.set_text(of.read())
        of.close()
        
    def _print(self, line):
        self._buffer.insert_at_cursor(line + '\n')

    def _insert(self, text, *tags):
        end_iter = self._buffer.get_end_iter()
        self._buffer.insert_with_tags_by_name(end_iter, text, *tags)
        
    def _print_file(self, filename, lineno, name):
        if filename.startswith(self._pwd):
            filename = filename.replace(self._pwd, '')[1:]

        self._insert('  File ')
        self._insert(filename, 'filename')
        self._insert(', line ')
        self._insert(str(lineno), 'lineno')
        self._insert(', in ')
        self._insert(name, 'name')
        self._insert('\n')
        
    def print_tb(self, tb, limit=None):
        """Print up to 'limit' stack trace entries from the traceback 'tb'.

        If 'limit' is omitted or None, all entries are printed.  If 'file'
        is omitted or None, the output goes to sys.stderr; otherwise
        'file' should be an open file or file-like object with a write()
        method.
        """

        if limit is None:
            if hasattr(sys, 'tracebacklimit'):
                limit = sys.tracebacklimit
        n = 0
        while tb is not None and (limit is None or n < limit):
            f = tb.tb_frame
            lineno = tb.tb_lineno
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            self._print_file(filename, lineno, name)
            line = linecache.getline(filename, lineno)
            if line:
                self._print('    ' + line.strip())
            tb = tb.tb_next
            n = n+1

    def _start_debugger(self):
        import pdb
        pdb.pm()

    def _on_send__clicked(self, button):
        exception_text = self._buffer.get_text(*self._buffer.get_bounds())
        if DebugWindow.application.send_bugreport(exception_text, self):
            # the bug was sent and we don't want the user to send it again
            self.send.set_sensitive(False)

    def _on_save__clicked(self, button):
        DebugWindow.application._save_cb(None)

    def _should_save_be_sensitive(self):
        #if not DebugWindow.application._project:
        #    return False

        #if not DebugWindow.application._project._changed:
        #    return False

        return True
    
def show(exctype, value, tb):
    if exctype is not KeyboardInterrupt:
        dw = DebugWindow()
        dw.show_exception(exctype, value, tb)
        dw.run()
        dw.destroy()

def show_log():
    dw = DebugWindow()
    dw.show_log()
    dw.notebook.set_current_page(1)
    dw.run()
    dw.destroy()

if __name__ == '__main__':
    dw = DebugWindow()
    resp = dw.run()
    print resp
    dw.destroy()

        

    
