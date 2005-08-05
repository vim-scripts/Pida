# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: plugin.py 478 2005-08-02 11:36:48Z aafshar $
#Copyright (c) 2005 George Cristian Bîrzan gcbirzan@wolfheart.ro

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

import os
import sys
import gtk
import logging

import pida.plugin as plugin
import pida.gtkextra as gtkextra
import pida.configuration.registry as registry
import pida.configuration.config as config

class Plugin(plugin.Plugin):
    NAME = "Boss"
    VISIBLE = False
    
    def configure(self, reg):
        self.ftregistry = reg.add_group('filetypes',
            'Determines which plugins are displayed for which filetypes.')
        self.ftregistry.add('all',
            registry.RegistryItem,
            'project, pastebin, gazpacho',
            'What plugins to always use (comma separated)')
        self.ftregistry.add('python',
            registry.RegistryItem,
            'python_browser, python_debugger, python_profiler',
            'What plugins to use only for python files (comma separated)')
        self.ftregistry.add('None',
            registry.RegistryItem,
            '',
            'What plugins to use on unknown files (comma separated)')

        self.plugregistry = reg.add_group('plugins',
            'Determines which plugins are loaded at startup.')
    
        for pluginname in self.prop_optional_pluginlist:
            self.plugregistry.add(pluginname,
                registry.Boolean,
                True,
                'Whether %s wil be loaded at startup (requires restart).' % \
                    pluginname)

    def do_init(self):
        self.filetypes = {}
        self.filetype_triggered = False
        self.filetype_current = 'None'

        self.log = logging.getLogger()
        self.loghandler = None
        #logging.basicConfig()
        self.evt_reset()
        #sys.stdout = sys.stderr = file('/dev/null', 'w')

        self.tips = gtk.Tooltips()
        self.tips.enable()

        self.child_processes = []

    def evt_populate(self):
        self.icons = gtkextra.Icons()

    def evt_shown(self):
        pass

    def evt_reset(self):
        self.reset_logger()
        self.reset_io()


    def reset_logger(self):
        logfile = self.prop_main_registry.files.log.value()
        if self.loghandler:
            self.log.removeHandler(self.loghandler)
        self.loghandler = logging.FileHandler(logfile)
        self.log.addHandler(self.loghandler)
        self.log.setLevel(self.prop_main_registry.log.level.value())
        
    def reset_io(self):
        stdiofile = '%s.io' % self.prop_main_registry.files.log.value()
        f = open(stdiofile, 'w')
        sys.stdout = sys.stderr = f

    def evt_bufferchange(self, buffernumber, buffername):
        if not self.filetype_triggered:
            self.filetypes[buffernumber] = 'None'
        if self.filetype_current != self.filetypes[buffernumber]:
            self.filetype_current = self.filetypes[buffernumber]
            self.pida.mainwindow.add_pages(self.get_pluginnames(self.filetype_current))
        self.filetype_triggered = False
        self.pida.mainwindow.set_title('PIDA %s' % buffername)
        
    def evt_filetype(self, buffernumber, filetype):
        self.filetype_triggered = True
        self.filetypes[buffernumber] = filetype

    def get_pluginnames(self, filetype):
        genplugins = [s.strip() for s in self.ftregistry.all.value().split(',')]
        ftplugins = []
        if hasattr(self.prop_main_registry.filetypes, filetype):
            fl = getattr(self.prop_main_registry.filetypes, filetype).value()
            ftplugins = [s.strip() for s in fl.split(',')]
            # No filetypes for the plugin
        return genplugins + ftplugins

    def get_named_plugin(self, name):
        for plugin in self.plugins:
            if plugin.NAME == name:
                return plugin

    def action_settip(self, widget, tiptext):
        self.tips.set_tip(widget, tiptext)

    def action_status(self, message):
        self.pida.mainwindow.statusbar.push(1, message)

    def do_log(self, source, message, level):
        """
        Log a message.
        """
        msg = '%s: %s' % (source, message)
        self.log.log(level, msg)

    def action_newbrowser(self, url):
        """
        Start a new browser
        """

    def action_showconfig(self, pagename=None):
        """ called to show the config editor """
        # Create a new configuration editor, and show it.
        self.configeditor = config.ConfigEditor()
        self.configeditor.show(pagename)

    def action_quit(self):
        """ Quit Pida. """
        # Tell plugins to die
        self.do_evt('die')
        # Fin
        for pid in self.child_processes:
            try:
                os.kill(pid, 15)
            except OSError:
                pass
        gtk.main_quit()

    def action_newterminal(self, commandline, **kw):
        """Open a new terminal, by issuing an event"""
        # Fire the newterm event, the terminal plugin will respond.
        self.do_evt('terminal', commandline, **kw)

    def action_fork(self, commandargs):
        print commandargs
        pid = os.fork()
        if pid == 0:
            try:
                os.execlp(commandargs[0], *commandargs)
            except Exception:
                pass
        else:
            self.child_processes.append(pid)

    def action_accountfork(self, pid):
        self.child_processes.append(pid)


