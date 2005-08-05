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

import pida.plugin as plugin
import pida.gtkextra as gtkextra
import gobject
import gtk
import os
import emacs

class Plugin(plugin.Plugin):
    NAME = 'Emacs'
    DICON = 'configure', 'Configure Pida'

    def init(self):
        self.emacs = emacs.EmacsClient(self.cb)

    def populate_widgets(self):
        self.add_button('editor', self.cb_launch, 'Run XEmacs', [])


    def cb_alternative(self, *args):
        self.cb.action_showconfig()

    def cb_launch(self, *args):
        self.emacs.launch()

    def edit_getbufferlist(self):
        """ Get the buffer list. """
        # Call the method of the vim communication window.
        self.emacs.get_bufferlist()

    def edit_getcurrentbuffer(self):
        self.emacs.get_currentbuffer()


    def edit_openfile(self, filename):
        self.emacs.edit_file(filename)


    def edit_changebuffer(self, buffernum):
        self.emacs.change_buffer(buffernum)

    def edit_gotoline(self, line):
        self.emacs.gotoline(line)
    
    def edit_closebuffer(self):
        self.emacs.close_buffer()

    #def edit_getcurrentbuffer(self):
    #    """ Ask Vim to return the current buffer number. """
    #    # Call the method of the vim communication window.
    #    self.cw.get_current_buffer(self.currentserver)

    #def edit_changebuffer(self, number):
    #    """Change buffer in the active vim"""
    #    self.cb.action_log('action', 'changebuffer', 0)
    #    # Call the method of the vim communication window.
    #    self.cw.change_buffer(self.currentserver, number)
    #    # Optionally foreground Vim.
    #    self.action_foreground()
   
    #def edit_foreground(self):
    #    """ Put vim into the foreground """
    #    # Check the configuration option.
    #    if int(self.opts.get('vim', 'foreground_jump')):
    #        # Call the method of the vim communication window.
    #        self.cw.foreground(self.currentserver)
 
    #def edit_openfile(self, filename):
    #    """open a new file in the connected vim"""
    #    self.cb.action_log('action', 'openfile', 0)
    #    # Call the method of the vim communication window.
    #    self.cw.open_file(self.currentserver, filename)

