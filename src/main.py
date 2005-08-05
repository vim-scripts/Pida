# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: main.py 482 2005-08-02 12:11:45Z aafshar $
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
import sys
import logging
import optparse

# Gtk
import gtk
import gobject

# Pida
import base
import mainwindow
import gtkextra
import firstrun
import configuration.options as options
import configuration.config as config
import configuration.registry as registry
# Version String
import pida.__init__
__version__ = pida.__init__.__version__

# Available plugins, could be automatically generated
OPTPLUGINS = ['project', 'python_browser', 'python_debugger', 'python_profiler',
'gazpacho', 'pastebin']

# Convenience method to ease importing plugin modules by name.
def create_plugin(name, cb):
    """ Find a named plugin and instantiate it. """
    # import the module
    # The last arg [True] just needs to be non-empty
    try:
        mod = __import__('pida.plugins.%s.plugin' % name, {}, {}, [True])
        try:
            inst = mod.Plugin()
        except Exception, e:
            logging.warn('Plugin "%s" failed to instantiate: %s' % (name, e))
            inst = None
    except ImportError, e:
        logging.warn('Plugin "%s" failed to import with: %s' % (name, e))
        inst = None

    return inst


class DummyOpts(object):
    """
    A dummy object to make the transition to the new registry
    """
    def __init__(self, cb):
        self.cb = cb

    def get(self, groupname, optname):
        group = getattr(self.cb.registry, groupname)
        option = getattr(group, optname)
        return option.value()

# Instance of this class is passed to every single custom object in Pida,
# as the cb parameter on instantiation.
# It is responsible for performing "actions" on the editor or other compnent
# and also for initiating "events" and propogating them to plugins.
class Application(base.pidaobject):
    """ The application class, a glue for everything """
    def __init__(self):
        base.set_application_instance(self)
        base.pidaobject.__init__(self)

    def do_init(self):
        # List of plugins loaded used for event passing
        self.plugins = []
        # convenience
        self.OPTPLUGINS = OPTPLUGINS
        # Main config options
        #self.opts = options.Opts()
        self.opts = DummyOpts(self)
        # Icons shared
        self.server = None
        self.startup()
        # start
        self.do_log('started', 20)

    def startup(self):
        sys.excepthook = debugwindow.show
        debugwindow.DebugWindow.application = self
        self.registry = registry.Registry(os.path.expanduser('~/.pida/pida.conf'))
        self.optparser = optparse.OptionParser()

       
        options.configure(self.registry)


        self.registry.prime_optparser(self.optparser)
        self.optparser.parse_args()
        self.registry.load()
        # now the base plugins

        self.do_first_time()

        self.boss = create_plugin('boss', self)
        self.boss.configure(self.registry)
        shell_plug = self.add_plugin('terminal')
        buffer_plug = self.add_plugin('buffer')


        opt_plugs = []
        for plugname in OPTPLUGINS:
            plugin = self.add_plugin(plugname)
            if plugin and plugin.VISIBLE:
                opt_plugs.append(plugin)
        
        # The editor 
        # editorname = 'vim'
        editorname = self.registry.components.editor.value()
        if not editorname in ['vim', 'culebra']:
            editorname = 'culebra'
        # using the registry can't ever work
        #if self.registry.general.emacsmode.value():
        self.set_editor(editorname)
       
        #self.evt('init')
       
        self.registry.load()
        self.registry.save()
      

        for pluginname in self.OPTPLUGINS:
            if not self.opts.get('plugins', pluginname):
                # slow but only once
                for plugin in self.plugins:
                    if plugin and plugin.NAME == pluginname:
                        self.plugins.remove(plugin)
                        opt_plugs.remove(plugin)

        self.mainwindow = mainwindow.MainWindow()

        self.evt('populate')
        self.mainwindow.set_plugins(self.editor, buffer_plug, shell_plug, opt_plugs)
        self.mainwindow.show_all()

        self.evt('shown')
        self.evt('started')
        self.evt('reset')
        

    def do_first_time(self):
        userdir = self.registry.directories.user.value()
        ftname = os.path.join(userdir, '.firsttime')
        if not os.path.exists(ftname):
            firsttimer = firstrun.FirstTimeWindow()
            firsttimer.show(ftname)


    def add_plugin(self, name):
        """
        Create and return the plugin
        """
        plugin = create_plugin(name, self)
        if plugin:
            plugin.configure(self.registry)
            self.plugins.append(plugin)
        return plugin

    def set_editor(self, name):
        """
        Set the editor plugin
        """
        self.editor = self.add_plugin(name)
        if self.editor:
            return self.editor
        else:
            raise Exception, 'Selected editor failed to load'

    def action(self, name, *args, **kw):
        self.do_log_debug('action: %s' % name)
        self.signal_to_plugin(self.boss, 'action', name, *args, **kw)

    def edit(self, name, *args, **kw):
        self.do_log_debug('edit: %s' % name)
        self.signal_to_plugin(self.editor, 'edit', name, *args, **kw)

    def evt(self, name, *args, **kw):
        """Callback for events from vim client, propogates them to plugins"""
        self.do_log_debug('evt: %s' % name)
        self.signal_to_plugin(self.boss, 'evt', name, *args, **kw)
        # pass the event to every plugin
        for plugin in self.plugins:
            # call the instance method, or an empty lambda
            self.signal_to_plugin(plugin, 'evt', name, *args, **kw)

    def signal_to_plugin(self, plugin, sigtype, signame, *args, **kw):
        funcname = '%s_%s' % (sigtype, signame)
        if hasattr(plugin, funcname):
            try:
                getattr(plugin, funcname)(*args, **kw)
                return True
            except Exception, e:
                print ('error passing %s "%s" to %s, %s' % (sigtype, signame,
                                                            plugin, e))
                return False
        return False


import debugwindow
def main(argv):
    a = Application()
    gtk.threads_init()
    gtk.main()

if __name__ == '__main__':
    main(sys.argv)



