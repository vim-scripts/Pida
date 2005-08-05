# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 431 2005-07-21 21:42:14Z aafshar $
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

"""
The Pida buffer explorer plugin
"""

# system imports
import os
import mimetypes
# GTK imports
import gtk
import gobject
# Pida imports
import pida.plugin as plugin
import pida.gtkextra as gtkextra

class BufferTree(gtkextra.Tree):
    '''
    Tree view control for buffer list.
    
    The displayed columns are the icon and shortened name.

    @var YPAD: Increase the default y-padding
    @var XPAD: Increase the default x-padding
    @var COLUMNS: The column template
    '''
    YPAD = 2
    XPAD = 2
    COLUMNS = [('icon', gtk.gdk.Pixbuf, gtk.CellRendererPixbuf, True,
                'pixbuf'),
               ('name', gobject.TYPE_STRING, gtk.CellRendererText, True,
                'markup'),
               ('file', gobject.TYPE_STRING, None, False, None),
               ('number', gobject.TYPE_INT, None, False, None)]

    def populate(self, bufferlist):
        '''
        Populate the list with the given buffer list.
        
        @param bufferlist: The list of buffers
        @type bufferlist: A list of (number, name) tuples
        '''
        self.clear()
        for buf in bufferlist:
            path = ''
            if len(buf) > 1:
                path = '%s' % buf[1]
            try:
                nr = int(buf[0])
                dirn, name = os.path.split(path)
                mtype = mimetypes.guess_type(path)[0]
            except ValueError:
                nr = 0
                name, dirn = ''
                mtype = None
            if mtype:
                mtype = mtype.replace('/','-')
                im = self.do_get_image(mtype).get_pixbuf()
            else:
                im = self.do_get_image('text-plain').get_pixbuf()
            markup = self.beautify(name, dirn, path)
            self.add_item([im, markup, path, nr])

    def beautify(self, name, dirn, path):
        if not name:
            name = 'untitled'
        pdir = os.path.split(dirn)[-1]
        MU = ('<span size="small">'
              '<span foreground="#0000c0">%s/</span>'
              '<b>%s</b>'
              '</span>')
        dirn = dirn.replace(os.path.expanduser('~'), '~')
        return MU % (pdir, name)


    def set_active(self, buffernumber):
        '''
        Set the selected element in the list by buffer number.
        
        @param buffernumber: The buffer number to show active.
        @type buffernumber: int
        '''
        for node in self.model:
            if node[3] == buffernumber:
                self.view.set_cursor(node.path)
                return True
        return False

class Plugin(plugin.Plugin):
    NAME = 'Buffers'
    DICON = 'refresh', 'Refresh the buffer list'
    
    def populate_widgets(self):
        """
        Put the additional widgets into the plugin.
        """
        # The list of buffers
        self.buffers = BufferTree()
        self.add(self.buffers.win)
        # The toolbar buttons
        self.add_button('open', self.cb_open, 'Open file')
        self.add_button('close', self.cb_close, 'Close Buffer')
        # The current buffer stored
        self.cbuf = None
        # The open-file dialog
        self.odialog = None

    def connect_widgets(self):
        """
        Connect the widget signals.
        """
        # Connect the click action of the buffer list
        self.buffers.connect_select(self.cb_bufs_selected)

    def refresh(self, bufferlist):
        '''
        Refresh the bufferlist.
        
        @param bufferlist: The list of buffers
        @type bufferlist: A list of (number, filename) pairs
        '''
        self.buffers.populate(bufferlist)

    def delayed_get_buffer(self, delay=1000):
        def get():
            self.do_edit('getbufferlist')
            return False
        # would grab it immediately, but it pays to wait.
        gobject.timeout_add(delay, get)


    def cb_alternative(self):
        '''
        Called when the detach button is clicked.
        '''
        # In our case the reload button.
        self.do_edit('getbufferlist')

    def cb_bufs_selected(self, tv):
        '''
        Called when an element in the buffer list is selected.
        '''
        # Which number is now selected
        sel = self.buffers.selected(3)
        # If it is not our current buffer, change to it
        if not self.cbuf or self.cbuf != sel:
            self.do_edit('changebuffer', sel)

    def cb_open(self, *args):
        '''
        Called when the open button is clicked.
        '''
        # Create a new open file dialogue if it does not exist
        if not self.odialog:
            self.odialog = gtkextra.FileDialog(self.cb_open_response)
            # Connect the window's destroy event
            self.odialog.connect('destroy', self.cb_open_destroy)
        # Show the open-file dialogue
        self.odialog.show()

    def cb_open_response(self, dialog, response):
        '''
        Called when a response is recived from the open dialog.
        '''
        # Hide the open dialogue
        self.odialog.hide()
        # Respond if the dialogue was accepted
        if response == gtk.RESPONSE_ACCEPT:
            # Get the name and open the file in Vim
            fn = self.odialog.get_filename()
            self.do_edit('openfile', fn)

    def cb_open_destroy(self, *args):
        '''
        Called when the open dialog is destroyed.
        '''
        self.odialog = None
        return True

    def cb_close(self, *a):
        '''
        Called when the close buffer button is clicked.
        '''
        # Close the active buffer.
        self.do_edit('closebuffer')
        self.delayed_get_buffer()

    def evt_bufferlist(self, bufferlist):
        '''
        Event: Called when a new buffer list is received.
        
        @param bufferlist: The list of buffers
        @type bufferlist: A list of (number, filename) pairs
        '''
        self.refresh(bufferlist)
        # New bufferlist may have new buffer
        if not self.buffers.set_active(self.cbuf):
            self.do_edit('getcurrentbuffer')

    def evt_bufferchange(self, buffernumber, name):
        '''
        Event: Called when the buffer number has changed.

        @param buffernumber: The buffer number.
        @type buffernumber: int

        @param name: The filename of the buffer
        @type name: str

        @param: 
        '''
        self.cbuf = int(buffernumber)
        # the new buffer may not be in our list
        if not self.buffers.set_active(self.cbuf):
            self.delayed_get_buffer(500)

    def evt_bufferunload(self, *a):
        '''
        Event: Called when a buffer is unloaded
        '''
        self.do_edit('getbufferlist')
    
    def evt_serverchange(self, server):
        '''
        Event: Called when the server is changed
        
        @param server: The name of the server
        @type server: str
        '''
        self.do_edit('getbufferlist')

    def evt_disconnected(self, *args):
        self.buffers.clear()

    def evt_switchfocus(self, *args):
        self.buffers.view.grab_focus()
