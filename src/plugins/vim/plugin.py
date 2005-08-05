# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 427 2005-07-21 19:54:24Z aafshar $
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
import gobject
# Pida imports
import pida.plugin as plugin
import pida.gtkextra as gtkextra
import pida.configuration.registry as registry
# local imports
import gdkvim
import vimembed

class Plugin(plugin.Plugin):
    NAME = 'Vim'
    RESIZABLE = False
    DICON = 'configure', 'Configure Pida'

    def configure(self, reg):
        self.registry = reg.add_group('vim', 'Options pertaining to the editor')

        self.registry.add('foreground_jump',
                  registry.Boolean,
                  1,
                  'Determines whether Pida will foreground Vim on actions.')
        self.registry.add('easy_mode',
                  registry.Boolean,
                  0,
                  'Determines whether Pida start Vim in Evim (easy mode).')
                  
                  
        self.registry.add('shutdown_with_vim',
                  registry.Boolean,
                  0,
                  'Determines whether Pida will shutdown when Vim shuts down.')

        self.registry.add('show_serverlist',
               registry.Boolean,
               False,
               'Determines whether the server bar will be shown in embedded '
               'mode. (embedded mode only)')

        shgrp = reg.add_group('vim_shortcuts', 'Shortcuts called from vim.')

        shgrp.add('shortcut_leader',
                  registry.RegistryItem,
                  ',',
                  'The value of the leasder key press')

        shgrp.add('shortcut_debug',
                  registry.RegistryItem,
                  'x',
                  'The shortcut to ')

        shgrp.add('shortcut_breakpoint_set',
                  registry.RegistryItem,
                  'b',
                  'The shortcut to ')

        shgrp.add('shortcut_breakpoint_clear',
                  registry.RegistryItem,
                  'B',
                  'The shortcut to ')

        shgrp.add('shortcut_execute',
                  registry.RegistryItem,
                  'x',
                  'The shortcut to ')

        shgrp.add('shortcut_project_execute',
                  registry.RegistryItem,
                  'p',
                  'The shortcut to ')

        shgrp.add('shortcut_doc_yanked',
                  registry.RegistryItem,
                  '/',
                  'The shortcut to ')

        shgrp.add('shortcut_doc_cursor',
                  registry.RegistryItem,
                  '?',
                  'The shortcut to ')
        
        shgrp.add('shortcut_pastebin_yanked',
                  registry.RegistryItem,
                  'm',
                  'The shortcut to paste the yanked text to a pastebin.')

        shgrp.add('shortcut_switch_focus',
            registry.RegistryItem,
            ',',
            'The shortcut to shift focust to the Pida controls')

    def populate_widgets(self):
        self.old_shortcuts = {'n':{}, 'v':{}}
        self.vim = None
        self.embedname = None
        #gobject.timeout_add(2000, self.cb_refresh)
        self.currentserver = None
        self.oldservers = []
        self.add_button('connect', self.cb_connect,
            'Connect to Vim session')
        self.add_button('editor', self.cb_run,
            'Execute a new Vim session')
        self.add_button('refresh', self.cb_refresh,
            'Refresh server list')
        self.entry = gtk.combo_box_new_text()
        self.add(self.entry, False)
        self.last_pane_position = 600
    
    def launch(self):
        vc = 'vim'
        if self.registry.easy_mode.value():
            vc = 'evim'
        vimcom = getattr(self.prop_main_registry.commands, vc).value()
        if self.is_embedded():
            if self.vim:
                self.message('Only one embedded Vim allowed.')
            else:
                name = self.generate_embedname()
                self.vim = vimembed.PidaVim(self.pida.embedwindow, vimcom, name)
                self.vim.connect(self.cb_plugged, self.cb_unplugged)
        else:
            os.system('%s --servername pida' % vimcom)

    def refresh(self, serverlist):
        if serverlist != self.oldservers:
            self.oldservers = serverlist
            actiter = self.entry.get_active_iter()
            act = None
            if actiter:
                act = self.entry.get_model().get_value(actiter, 0)
            self.entry.get_model().clear()
            for i in serverlist:
                s = i.strip()
                if self.is_embedded():
                    if s == self.embedname:
                        self.entry.append_text(s.strip())
                        if self.currentserver != s:
                            self.connectserver(s)
                else:
                    self.entry.append_text(s.strip())
            if act:
                for row in self.entry.get_model():
                    if row[0] == act:
                        self.entry.set_active_iter(row.iter)
            else:
                self.entry.set_active(0)
            if not self.currentserver:
                server = None
                if not self.is_embedded():
                    if serverlist:
                        server = serverlist[0]
                self.connectserver(server)

    def connectserver(self, name):
        # Actually does the connecting
        if name:
            self.currentserver = name
            self.load_shortcuts()
            self.cw.send_ex(self.currentserver, '%s' % VIMSCRIPT)
            self.do_evt('serverchange', name)
        else:
            # Being asked to connect to None is the same as having nothing
            # to connect to.
            self.do_evt('disconnected', name)

    def fetchserverlist(self):
        """Get the list of servers"""
        # Call the method of the vim communication window.
        self.cw.fetch_serverlist()

    def load_shortcuts(self):
        for mapc in ['n', 'v']:
            if self.old_shortcuts[mapc].setdefault(self.currentserver, []):
                for sc in self.old_shortcuts[mapc][self.currentserver]:
                    self.cw.send_ex(self.currentserver, UNMAP_COM % (mapc, sc))
            self.old_shortcuts[mapc][self.currentserver] = []
            l = self.prop_main_registry.vim_shortcuts.shortcut_leader.value()
            for name, command in SHORTCUTS:
                c = getattr(self.prop_main_registry.vim_shortcuts, name).value()
                sc = ''.join([l, c])
                self.old_shortcuts[mapc][self.currentserver].append(sc)
                self.cw.send_ex(self.currentserver, NMAP_COM % (mapc, sc, command))

    def generate_embedname(self):
        self.embedname = 'PIDA_EMBED_%s' % time.time()
        return self.embedname

    def is_embedded(self):
        return self.prop_main_registry.layout.embedded_mode.value()

    def cb_plugged(self):
        self.pida.embedslider.set_position(self.last_pane_position)

    def cb_unplugged(self):
        self.last_pane_position = self.pida.embedslider.get_position()
        self.pida.embedslider.set_position(0)
        self.vim = None

    def cb_connect(self, *a):
        iter = self.entry.get_active_iter()
        if iter:
            name = self.entry.get_model().get_value(iter, 0)
            self.connectserver(name)
   
    def cb_refresh(self, *args):
        self.fetchserverlist()
        return True

    def cb_run(self, *args):
        self.launch()

    def cb_alternative(self, *args):
        self.do_action('showconfig')

    def show_or_hide_serverlist(self):
        if self.is_embedded():
            if self.registry.show_serverlist.value():
                self.entry.show()
            else:
                self.entry.hide()

    def evt_die(self):
        if self.is_embedded():
            pass
            #self.cw.quit(self.currentserver)

    def evt_reset(self):
        if self.embedded_value != self.prop_main_registry.layout.embedded_mode.value():
            self.message('Embedded mode setting has changed.\n'
                         'You must restart Pida.')
            return
        self.load_shortcuts()
        self.show_or_hide_serverlist()

    def evt_started(self, *args):
        self.cw = gdkvim.VimWindow()
        self.embedded_value = self.prop_main_registry.layout.embedded_mode.value()
        if self.is_embedded():
            self.launch()

    def evt_serverlist(self, serverlist):
        self.refresh(serverlist)

    def evt_vimshutdown(self, *args):
        if self.is_embedded():
            # Check if users want shutdown with Vim
            if self.registry.shutdown_with_vim.value():
                # Quit pida
                self.do_action('quit')
                # The application never gets here
        del self.old_shortcuts['n'][self.currentserver]
        del self.old_shortcuts['v'][self.currentserver]
        self.currentserver = None
        self.cb_refresh()

    def evt_serverchange(self, name):
        self.currentserver = name

    def evt_editorfocus(self):
        self.cw.foreground(self.currentserver)

    def edit_closebuffer(self):
        """ Close the current buffer. """
        # Call the method of the vim communication window.
        self.cw.close_buffer(self.currentserver)

    def edit_gotoline(self, line):
        # Call the method of the vim communication window.
        self.cw.change_cursor(self.currentserver, 1, line)
        # Optionally foreground Vim.
        self.edit_foreground()

    def edit_getbufferlist(self):
        """ Get the buffer list. """
        # Call the method of the vim communication window.
        self.cw.get_bufferlist(self.currentserver)

    def edit_getcurrentbuffer(self):
        """ Ask Vim to return the current buffer number. """
        # Call the method of the vim communication window.
        self.cw.get_current_buffer(self.currentserver)

    def edit_changebuffer(self, number):
        """Change buffer in the active vim"""
        # Call the method of the vim communication window.
        self.cw.change_buffer(self.currentserver, number)
        # Optionally foreground Vim.
        self.cw.foreground(self.currentserver)
   
    def edit_foreground(self):
        """ Put vim into the foreground """
        # Check the configuration option.
        if self.registry.foreground_jump.value():
            # Call the method of the vim communication window.
            self.cw.foreground(self.currentserver)
 
    def edit_openfile(self, filename):
        """open a new file in the connected vim"""
        # Call the method of the vim communication window.
        self.cw.open_file(self.currentserver, filename)

    def edit_preview(self, filename):
        self.cw.preview_file(self.currentserver, filename)

    def edit_newterminal(self, command, args, **kw):
        """Open a new terminal, by issuing an event"""
        # Fire the newterm event, the terminal plugin will respond.
        self.evt('newterm', command, args, **kw)

    def edit_quitvim(self):
        """
        Quit Vim.
        """
        self.cw.quit(self.currentserver)


SHORTCUTS = [('shortcut_execute',
                'Async_event("bufferexecute,")'),
             ('shortcut_project_execute',
                'Async_event("projectexecute,")'),
             ('shortcut_breakpoint_set',
                'Async_event("breakpointset,".line("."))'),
             ('shortcut_breakpoint_clear',
                'Async_event("breakpointclear,".line("."))'),
             ('shortcut_doc_yanked',
                '''Async_event("doc,".expand('<cword>'))'''),
             ('shortcut_doc_cursor',
                'Async_event("doc,".@")'),
             ('shortcut_pastebin_yanked',
                '''Async_event("pastebin,".@")'''),
             ('shortcut_switch_focus',
                'Async_event("switchfocus,")')]

NMAP_COM = '%smap %s :call %s<lt>CR>'

UNMAP_COM = '%sun %s'

VIMSCRIPT = ''':silent function! Bufferlist()
let i = 1
    let max = bufnr('$') + 1
    let lis = ""
    while i < max
        if bufexists(i)
            let lis = lis.";".i.":".bufname(i)
        endif
        let i = i + 1
    endwhile
    return lis
endfunction
:silent function! Yank_visual()
    y
    return @"
endfunction
:silent function! Async_event(e)
    let c = "call server2client('".expand('<client>')."', '".a:e."')"
    try
        exec c
    catch /.*/
        echo c
    endtry
endfunction
:silent augroup pida
:silent au! pida
:silent au pida BufEnter * call Async_event("bufferchange,".bufnr('%').",".bufname('%'))
:silent au pida BufDelete * call Async_event("bufferunload,")
:silent au pida VimLeave * call Async_event("vimshutdown,")
:silent au pida FileType * call Async_event("filetype,".bufnr('%').",".expand('<amatch>'))
:echo "PIDA connected"
'''

