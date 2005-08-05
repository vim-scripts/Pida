# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: config.py 480 2005-08-02 11:42:54Z aafshar $
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

"""Provides the widgets for dynamically generating a configuration editor."""

# GTK import
import gtk
# System imports
import textwrap
#Pida imports
import pida.base as base
import pida.gtkextra as gtkextra

class ConfigWidget(base.pidaobject):
    """
    A widget holder which can save or load its state.
    
    This class is largely abstract, and must be overriden for useful use. See
    the examples below.
    """
    def do_init(self, widget, option):
        """
        Constructor
        
        @param cb: An instance of the application class
        @type cb: pida.main.Application

        @param widget: The actual widget for the holder.
        @type widget: gtk.Widget
        """
        self.option = option
        # Build the widget
        # Containers
        self.win = gtk.VBox()
        hb = gtk.HBox()
        self.win.pack_start(hb)
        # Name label
        self.name_l = gtk.Label()
        self.name_l.set_markup('<span weight="bold">'
                               '%s</span>' % self.get_name())
        hb.pack_start(self.name_l, padding=4, expand=True)
        self.name_l.set_size_request(100, -1)
        # Actual widget
        self.widget = widget
        hb.pack_start(widget, padding=4)
        hb2 = gtk.HBox()
        self.win.pack_start(hb2)
        # Help label
        self.help_l = gtk.Label()
        self.help_l.set_markup(self.get_help())
        hb2.pack_start(self.help_l, expand=False, padding=4)

    def get_name(self):
        """
        Return a beautified name for the configuration option.
        """
        return self.option._name.replace('_', ' ')
   
    def get_help(self):
        """
        Return the help for the option.
        """
        help = self.option.doc
        return '\n'.join(textwrap.wrap(help, 60))

    def set_value(self, value):
        """
        Set the configuration value to the widget's value.

        @param value: The value to set the widget to.
        @type value: string
        """
        self.option.set(value)
    
    def value(self):
        """
        Get the configuration value from the options database.
        """
        return self.option.value()

    def load(self):
        """
        Called to load data from the options database into the widget.
        """
        pass

    def save(self):
        """
        Called to save data from the widget into the opitons database.
        """
        pass

class ConfigEntry(ConfigWidget):
    """
    An entry widget for plain configuration strings.
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtk.Entry()
        ConfigWidget.do_init(self, widget, option)

    def load(self):
        """
        Set the entry widget text to the option database value.
        """
        self.widget.set_text('%s' % self.value())

    def save(self):
        """
        Set the option database value to the widgets text.
        """
        self.set_value(self.widget.get_text())

class ConfigBoolean(ConfigWidget):
    """
    A checkbox widget forr boolean configuration values.
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtk.CheckButton(label="Yes")
        ConfigWidget.do_init(self, widget, option)
       
    def stob(self, s):
        """
        Convert a string to a boolean. 
        
        This method is deprecated and should not be used
        """
        return s.lower().startswith('t')
 
    def load(self):
        """
        Load the checkbox active status from the options database.
        """
        self.widget.set_active(self.value())

    def save(self):
        """
        Save the checkbox active state to the options database.
        """
        self.set_value(self.widget.get_active())

class ConfigFont(ConfigWidget):
    """
    A font selection dialogue that takes its values from the config database.
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtk.FontButton()
        ConfigWidget.do_init(self, widget, option)
        
    def load(self):
        """
        Load th font value from the options database.
        """
        fn = self.value()
        self.widget.set_font_name(fn)

    def save(self):
        """
        Save the font value to the options database.
        """
        self.set_value(self.widget.get_font_name())

class ConfigFile(ConfigWidget):
    """
    A widget that represents a file selection entry and dialogue button.
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtkextra.FileButton()
        ConfigWidget.do_init(self, widget, option)
        
    def load(self):
        """
        Load the filename from the options database.
        """
        fn = self.value()
        self.widget.set_filename(fn)

    def save(self):
        """
        Save the filename to the options database.
        """
        self.set_value(self.widget.get_filename())

class ConfigFolder(ConfigFile):
    """
    A widget that represents a directory entry and dialogue button.
    
    (Note called "Folder" because GTK calls it a "Folder").
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtkextra.FolderButton()
        ConfigWidget.do_init(self, widget, option)
       
class ConfigColor(ConfigWidget):
    """
    A widget for a colour selection button and dialogue.
    """
    def do_init(self, option):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param section: The configuration section that the widget is for.
        @type section: string

        @param key: The configuration key that the widget is for
        @type key: string
        """
        widget = gtk.ColorButton()
        ConfigWidget.do_init(self, widget, option)

    def load(self):
        """
        Load the colour from the options database.
        """
        cn = self.value()
        col = self.widget.get_colormap().alloc_color(cn)
        self.widget.set_color(col)

    def save(self):
        """
        Save the colour to the options database.
        """
        c = self.widget.get_color()
        v = gtk.color_selection_palette_to_string([c])
        self.set_value(v)

class ConfigInteger(ConfigEntry):
    MIN = 0
    MAX = 99
    STEP = 1
    
    def do_init(self, option):
        if hasattr(option, 'adjustment'):
            adjvals = option.adjustment
        else:
            adjvals = self.MIN, self.MAX, self.STEP
        adj = gtk.Adjustment(0, *adjvals)
        widget = gtk.SpinButton(adj)
        ConfigWidget.do_init(self, widget, option)

    def load(self):
        """
        Set the entry widget text to the option database value.
        """
        self.widget.set_value(self.value())

    def save(self):
        """
        Set the option database value to the widgets text.
        """
        self.set_value(int(self.widget.get_value()))

class ConfigList(ConfigEntry):
    def do_init(self, option):
        widget = gtk.combo_box_new_text()
        if hasattr(option, 'choices'):
            for choice in getattr(option, 'choices'):
                widget.append_text(choice)
        ConfigWidget.do_init(self, widget, option)
                
    def load(self):
        for i, row in enumerate(self.widget.get_model()):
            if row[0] == self.value():
                self.widget.set_active(i)
                break

    def save(self):
        actiter = self.widget.get_active_iter()
        act = None
        if actiter:
            act = self.widget.get_model().get_value(actiter, 0)
        self.set_value(act)

class ListTree(base.pidaobject, gtk.TreeView):
    """
    A treeview control for switching a notebook's tabs.
    """
    def do_init(self, configeditor):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application

        @param configeditor: The configuration editor that the list is used
            for.
        @type configeditor: pida.config.ConfigEditor
        """
        self.configeditor = configeditor
        self.store = gtk.ListStore(str, int)
        gtk.TreeView.__init__(self, self.store)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", renderer, markup=0)
        self.append_column(column)
        self.set_headers_visible(False)
        self.connect('cursor-changed', self.cb_select)

    def cb_select(self, *args):
        """
        Callback when an item in the list is selected.
        """
        path = self.store.get_iter(self.get_cursor()[0])
        tid = self.store.get_value(path, 1)
        # call the config editor's callback
        self.configeditor.cb_select(tid)

    def populate(self, names):
        """
        Populate the list with the required names.
        """
        self.store.clear()
        for name, i in names:
            s = '%s' % name
            self.store.append((s, i))

class ConfigEditor(base.pidaobject):
    """
    A top-level window containing dynamically generated controls for
    configuration information from the Pida options database.
    """
    def do_init(self):
        """
        Constructor.
        
        @param cb: An instance of the application class.
        @type cb: pida.main.Application
        """
        # main window
        self.win = gtk.Window()
        self.win.set_title('PIDA Configuration Editor')
        self.win.set_transient_for(self.pida.mainwindow)
        self.win.connect('destroy', self.cb_cancel)
        # top container
        hbox = gtk.HBox()
        self.win.add(hbox)
        self.lmodel = gtk.ListStore(str, int)
        self.tree = ListTree(self)
        hbox.pack_start(self.tree, expand=False, padding=6)
        vbox = gtk.VBox()
        hbox.pack_start(vbox)
        # notebook
        self.nb = gtk.Notebook()
        vbox.pack_start(self.nb, padding=4)
        self.nb.set_show_tabs(False)
        # Button Bar
        cb = gtk.HBox()
        vbox.pack_start(cb, expand=False, padding=2)
        # separator
        sep = gtk.HSeparator()
        cb.pack_start(sep)
        # cancel button
        self.cancel_b = gtk.Button(stock=gtk.STOCK_CANCEL)
        cb.pack_start(self.cancel_b, expand=False)
        self.cancel_b.connect('clicked', self.cb_cancel)
        # reset button
        self.reset_b = gtk.Button(stock=gtk.STOCK_UNDO)
        cb.pack_start(self.reset_b, expand=False)
        self.reset_b.connect('clicked', self.cb_reset)
        # apply button
        self.apply_b = gtk.Button(stock=gtk.STOCK_APPLY)
        cb.pack_start(self.apply_b, expand=False)
        self.apply_b.connect('clicked', self.cb_apply)
        # save button
        self.save_b = gtk.Button(stock=gtk.STOCK_SAVE)
        cb.pack_start(self.save_b, expand=False)
        self.save_b.connect('clicked', self.cb_save)
        self.controls = {}
        
        self.setopts()
        self.initialize()

    def setopts(self):
        self.registry = self.prop_main_registry

    def initialize(self):
        """
        Load the initial database options into the config editor, and generate
        the required widgets.
        """
        pages = []
        for group in self.registry.iter_groups():
        
        #sects =  self.opts.sections()
        #sects.sort()
        #for section in sects:
            box = gtk.VBox()
            sectlab = ''.join([group._name[0].upper(), group._name[1:]])
            sectdoc = gtk.Label(group._doc)
            box.pack_start(sectdoc, expand=False)
            
            tabid = self.nb.append_page(box, gtk.Label(sectlab))
            pages.append((sectlab, tabid))
            for option in group:
                #ctype = TYPES[self.get_type(section, opt)]
                cw = option.DISPLAY_WIDGET(option)
                box.pack_start(cw.win, expand=False, padding=4)
                self.controls[(group._name, option._name)] = cw
                box.pack_start(gtk.HSeparator(), expand=False, padding=4)
        self.tree.populate(pages)

    def get_type(self, section, option):
        return self.opts.types[(section, option)]

    def load(self):
        """
        Load the configuration information from the database.
        """
        #for group, option in self.registry.iter_items():
        #for section in self.opts.sections():
        #    for opt in self.opts.options(section):
        for k in self.controls:
            self.controls[k].load()

    def save(self):
        """
        Save the configuration information to the database.
        """
        for k in self.controls:
            self.controls[k].save()
        self.registry.save()
        #for section in self.opts.sections():
        #    for opt in self.opts.options(section):
        #        self.controls[(section, opt)].save()
        #self.opts.write()
        self.do_evt('reset')

    def show(self, pagename=None):
        self.load()
        self.win.show_all()
        if pagename:
            for row in self.tree.get_model():
                name, i = row
                if name.lower() == pagename.lower():
                    self.nb.set_current_page(i)
                    self.tree.set_cursor(row.path)
                    break

    def hide(self):
        self.win.hide_all()
        self.win.destroy()

    def cb_select(self, tid):
        self.nb.set_current_page(tid)

    def cb_reset(self, *args):
        self.show()

    def cb_apply(self, *args):
        self.save()

    def cb_cancel(self, *args):
        self.hide()

    def cb_save(self, *args):
        self.save()
        self.hide()


if __name__ == '__main__':
    w = ConfigEditor(None)
    w.show()
    gtk.main()
