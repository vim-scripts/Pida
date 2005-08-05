# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 473 2005-07-29 15:25:35Z snmartin $
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
import time
# GTK imports
import gtk
import pango
import gnomevfs
import gobject
# Pida imports
import pida.plugin as plugin
import pida.gtkextra as gtkextra
import pida.configuration.config as config
import pida.configuration.registry as registry

import edit

class Plugin(plugin.Plugin):
    NAME = 'Culebra'    
    DICON = 'configure', 'Configure Pida'

    def configure(self, reg):
        self.personal_registry = reg.add_group('culebra',
            'options pertaining to the Culebra editor')

        self.personal_registry.add('font',
            registry.Font,
            'Monospace 10',
            'The Font used by Culebra')

    def do_init(self):
        self.editor = None
        self.bufferlist = None
        self.currentbufnum = None

    def launch(self):
        self.create_editor()
        self.edit_getbufferlist()

    def create_editor(self):
        if not self.editor:
            self.editor = edit.EditWindow(self)
            self.pida.embedwindow.add(self.editor)
            self.editor.show_all()
        
    def populate_widgets(self):
        pass

    def cb_alternative(self, *args):
        self.do_action('showconfig')
    
    def evt_reset(self):
        font = self.personal_registry.font.value()
        font_desc = pango.FontDescription(font)
        if font_desc:
            self.editor.editor.modify_font(font_desc)

    def check_mime(self, fname):
        try:
            buff, fn = self.editor.get_current()
            manager = buff.get_data('languages-manager')
            if os.path.isabs(fname):
                path = fname
            else:
                path = os.path.abspath(fname)
            uri = gnomevfs.URI(path)
            mime_type = gnomevfs.get_mime_type(path) # needs ASCII filename, not URI
            if mime_type:
                language = manager.get_language_from_mime_type(mime_type)
                if language:
                    return language.get_name().lower()
        except Exception, e:
            pass
        return 'None'

    def evt_started(self):
        self.launch()
        
    def evt_debuggerframe(self, frame):
        if not frame.filename.startswith('<'):
            if frame.filename != self.editor.get_current()[0]:
                self.do_edit('openfile', frame.filename)
            self.do_edit('gotoline', frame.lineno - 1)
        
    def edit_getbufferlist(self):
        bl = [(i, v[1]) for (i, v) in enumerate(self.editor.wins)]
        self.bufferlist = bl
        self.do_evt('bufferlist', bl)

    def abspath(self, filename):
        if filename and not filename.startswith('/'):
            filename = os.path.join(os.getcwd(), filename)
        return filename

    def edit_getcurrentbuffer(self):
        fn = self.editor.get_current()[1]
        self.do_evt('filetype', self.editor.current_buffer, self.check_mime(fn))
        self.do_evt('bufferchange', self.editor.current_buffer, fn)

    def edit_changebuffer(self, num):
        if self.editor.current_buffer != num:
            self.editor.current_buffer = num
            buff = self.editor.wins[self.editor.current_buffer][0]
            self.editor.editor.set_buffer(self.editor.wins[num][0])
            self.edit_getcurrentbuffer()
            self.editor.editor.scroll_to_mark(buff.get_insert(), 0.25)
            self.editor.editor.grab_focus()    

    def edit_closebuffer(self):
        self.editor.file_close()

    def edit_gotoline(self, line):
        buf = self.editor.get_current()[0]
        titer = buf.get_iter_at_line(line)
        self.editor.editor.scroll_to_iter(titer, 0.25)
        buf.place_cursor(titer)
        self.editor.editor.grab_focus()

    def edit_openfile(self, filename):
        self.editor.load_file(filename)
