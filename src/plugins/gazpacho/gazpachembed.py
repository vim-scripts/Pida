# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: gazpachembed.py 352 2005-07-14 00:16:02Z gcbirzan $
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

"""stolen almost entirely from gazpacho. It is horrible It will look better one day, I just
need to know exactly what is needed."""

import gtk
import os
import gettext
from gazpacho.path import languages_dir

def init_l10n():
    gettext.install('gazpacho', languages_dir, unicode=True)

# we need to call this before anything else because in some Gazpacho classes
# there are l10n strings and so they need the _ function in loading time
init_l10n()
from gazpacho import application, gladegtk
from gazpacho.path import pixmaps_dir
from gazpacho import palette, editor, project, catalog
from gazpacho.gaction import GActionsView, GAction, GActionGroup
class Gazpacho(object):

    def __init__(self, cb):
        self.cb = cb
        self.app = None
        self.holder = None

    def launch(self, holder=None):
        if not application:
            print 'gazpacho not installed'
            return
        if not self.app:
            if holder:
                self.app = GazpachoEmbedded(self.cb)
                self.app.undo_button = self.undo_button
                self.app.redo_button = self.redo_button
                self.app._pidawindow = self.cb.mainwindow
                holder.pack_start(self.app._window)
                self.holder = holder
            else:
                self.app = GazpachoApplication()
            self.app.reactor = self
        self.app.show_all()
        self.app.new_project()


class GazpachoApplication(application.Application):

    def _quit_cb(self, action=None):
        projects = self._projects
        for project in projects:
            if project.changed:
                if not self._confirm_close_project(project):
                    return
                self._projects.remove(project)
        self._window.hide_all()

class GazpachoEmbedded(GazpachoApplication):
    
    def __init__(self, cb):
        self.cb = cb
        GazpachoApplication.__init__(self)

    def _change_action_state(self, sensitive=[], unsensitive=[]):

        """Set sensitive True for all the actions whose path is on the
        sensitive list. Set sensitive False for all the actions whose path
        is on the unsensitive list.
        """
        pass
        #for action_path in sensitive:
        #    action = self._ui_manager.get_action(action_path)
        #    action.set_property('sensitive', True)
        #for action_path in unsensitive:
        #    action = self._ui_manager.get_action(action_path)
        #    action.set_property('sensitive', False)            

    def get_window(self): return self._pidawindow
    window = property(get_window)
    
    def _refresh_title(self):
        return
        if self._project:
            title = 'Gazpacho - %s' % self._project.name
        else:
            title = 'Gazpacho'
        self._window.set_title(title)

    def _application_window_create(self):
        
        application_window = gtk.VBox()
        #application_window.move(0, 0)
        #application_window.set_default_size(700, -1)
        #gtk.window_set_default_icon_from_file(join(pixmaps_dir,
        #                                           'gazpacho-icon.png'))
        #application_window.connect('delete-event', self._delete_event)

        # Create the different widgets
        menubar = self._construct_menu_and_toolbar(application_window)

        self._palette = MiniPalette(self.cb, self._catalogs)
        self._palette.connect('toggled', self._palette_button_clicked)

        ebox = gtk.VBox()
        self.editor_combo = gtk.combo_box_new_text()
        ebox.pack_start(self.editor_combo, expand=False)
        
        self._editor = editor.Editor(self)
        self._editor.set_show_tabs(False)
        ebox.pack_start(self._editor)

        for i in range(self._editor.get_n_pages()):
            page = self._editor.get_nth_page(i)
            label = self._editor.get_tab_label_text(page)
            self.editor_combo.append_text(label)
        self.editor_combo.set_active(0)
        self.editor_combo.connect('changed', self.cb_editor_selected)
        
        widget_view = self._widget_tree_view_create()

        self.gactions_view = self._gactions_view_create()
        
        self._statusbar = self._construct_statusbar()

        # Layout them on the window
        main_vbox = gtk.VBox()
        application_window.add(main_vbox)

        top_box = gtk.HBox()
        main_vbox.pack_start(top_box, expand=False)

        #top_box.pack_start(toolbar)
        #top_box.pack_start(menubar, False)
        self.menu = menubar

        hbox = gtk.VBox(spacing=6)

        
        self.selector_image = gtk.Image()
        self.selector_image.set_from_file(os.path.join(pixmaps_dir, 'selector.png'))

        self.expander_label = ExpanderLabel(self.cb, self.selector_image)
        #hbox.pack_start(self.expander_label, expand=False)
        
        hbox2 = gtk.HBox()

        hbox.pack_start(hbox2, expand=False)
        self._palette_expander = gtk.Expander()
        self._palette_expander.set_label_widget(self.expander_label)
        self._palette_expander.add(self._palette)
        hbox2.pack_start(self._palette_expander)
        self._palette_expander.set_expanded(True)

        self.selector = self._palette._selector
        #self.selector.set_mode(False)
        #self.selector.set_active(True)
        #self.selector.set_relief(gtk.RELIEF_NONE)
        #self.selector.add(get_resized_image_copy(self.selector_image, 14))
        #self.selector.connect('toggled', self.cb_selector)
        hbox2.pack_start(self.selector, expand=False)


        
        vpaned = gtk.VPaned()
        hbox.pack_start(vpaned, True, True)

        notebook = gtk.Notebook()
        notebook.append_page(widget_view, gtk.Label(('Widgets')))
        notebook.append_page(self.gactions_view, gtk.Label(('Actions')))
        notebook.set_size_request(200, -1)

        #vpaned.set_position(200)

        vpaned.pack1(notebook, True, True)
        vpaned.pack2(ebox, True, True)
        self._editor.set_size_request(200, -1)

        main_vbox.pack_start(hbox)
        
        #main_vbox.pack_end(self._statusbar, False)

        #self.refresh_undo_and_redo()

        self._editor._load_signal_page()
        self.signals_list = self._editor._signal_editor._signals_list
        self.signals_list.connect('row-activated', self.cb_signal_activated)

        return application_window

    def cb_signal_activated(self, tv, path, column):
        model = tv.get_model()
        niter = model.get_iter(path)
        callbackname = model.get_value(niter, 1)
        widgetname = self._editor._loaded_widget.name
        widgettype =  self._editor._loaded_widget.gtk_widget
        signalname =  model.get_value(niter, 0)
        if callbackname.startswith('<'):
            callbackname = '%s_%s' % (widgetname, signalname.replace('-', '_'))
            model.set_value(niter, 1, callbackname)
        if callbackname:
            if not self._project.path:
                mb = gtk.MessageDialog(parent=self.get_window(),
                        flags = 0,
                        type = gtk.MESSAGE_INFO,
                        buttons = gtk.BUTTONS_OK,
                        message_format='You must save your user interface '
                                       'file before continuing.')
                def mbok(*args):
                    mb.destroy()
                mb.connect('response', mbok)
                mb.run()
                self._save_cb(None)
            if not self._project.path:
                return
            self.cb.evt('signaledited', self._project.path,
                            widgetname,
                            widgettype,
                            signalname,
                            callbackname)
        #print self._project.path


    def cb_editor_selected(self, button):
        page = self.editor_combo.get_active()
        self._editor.set_current_page(page)
 
    def cb_selector(self, button):
        #if not self.selector.get_active():
        #    self.selector.set_active(True)
        #    return
        self._palette._on_button_toggled(self._palette._selector, True)
 
    def _palette_button_clicked(self, palette):
        klass = palette.current

        # klass may be None if the selector was pressed
        self._add_class = klass
        if klass and klass.is_toplevel():
            self._command_manager.create(klass, None, self._project)
            self._palette.unselect_widget()
            self._add_class = None
        
        self.expander_label.set_label(self._add_class)
        if self._add_class:
            self.selector.set_active(False)
           
            

    def _construct_menu_and_toolbar(self, application_window):
        actions =(
            ('Gazpacho', None, ('_Gaz')),
            ('FileMenu', None, ('_File')),
            ('New', gtk.STOCK_NEW, ('_New'), '<control>N',
             ('New Project'), self._new_cb),
            ('Open', gtk.STOCK_OPEN, ('_Open'), '<control>O',
             ('Open Project'), self._open_cb),
            ('Save', gtk.STOCK_SAVE, ('_Save'), '<control>S',
             ('Save Project'), self._save_cb),
            ('SaveAs', gtk.STOCK_SAVE_AS, ('_Save As...'),
             '<shift><control>S', ('Save project with different name'),
             self._save_as_cb),
            ('Close', gtk.STOCK_CLOSE, ('_Close'), '<control>W',
             ('Close Project'), self._close_cb),
            ('Quit', gtk.STOCK_QUIT, ('_Quit'), '<control>Q', ('Quit'),
             self._quit_cb),
            ('EditMenu', None, ('_Edit')),
            ('Cut', gtk.STOCK_CUT, ('C_ut'), '<control>X', ('Cut'),
             self._cut_cb),
            ('Copy', gtk.STOCK_COPY, ('_Copy'), '<control>C', ('Copy'),
             self._copy_cb),
            ('Paste', gtk.STOCK_PASTE, ('_Paste'), '<control>V', ('Paste'),
             self._paste_cb),
            ('Delete', gtk.STOCK_DELETE, ('_Delete'), '<control>D',
             ('Delete'), self._delete_cb),
            ('ActionMenu', None, ('_Actions')),
            ('AddAction', gtk.STOCK_ADD, ('_Add action'), '<control>A',
             ('Add an action'), self._add_action_cb),
            ('RemoveAction', gtk.STOCK_REMOVE, ('_Remove action'), None,
             ('Remove action'), self._remove_action_cb),
            ('EditAction', None, ('_Edit action'), None, ('Edit Action'),
             self._edit_action_cb),
            ('ProjectMenu', None, ('_Project')),
            ('DebugMenu', None, ('_Debug')),
            ('HelpMenu', None, ('_Help')),
            ('About', None, ('_About'), None, ('About'), self._about_cb)
            )

        toggle_actions = (
            ('ShowCommandStack', None, ('Show _command stack'), 'F3',
             ('Show the command stack'), self._show_command_stack_cb, False),
            ('ShowClipboard', None, ('Show _clipboard'), 'F4',
             ('Show the clipboard'), self._show_clipboard_cb, False),
            )
        
        undo_action = (
            ('Undo', gtk.STOCK_UNDO, ('_Undo'), '<control>Z',
             ('Undo last action'), self._undo_cb),
            )

        redo_action = (
            ('Redo', gtk.STOCK_REDO, ('_Redo'), '<control>R',
             ('Redo last action'), self._redo_cb),
            )
        
        ui_description = """<ui>
              <menubar name="MainMenu">
                <menu action="Gazpacho">
                <menu action="FileMenu">
                  <menuitem action="New"/>
                  <menuitem action="Open"/>
                  <separator name="FM1"/>
                  <menuitem action="Save"/>
                  <menuitem action="SaveAs"/>
                  <separator name="FM2"/>
                  <menuitem action="Close"/>
                  <menuitem action="Quit"/>
                </menu>
                <menu action="EditMenu">
                  <menuitem action="Undo"/>
                  <menuitem action="Redo"/>
                  <separator name="EM1"/>
                  <menuitem action="Cut"/>
                  <menuitem action="Copy"/>
                  <menuitem action="Paste"/>
                  <menuitem action="Delete"/>
                </menu>
                <menu action="ActionMenu">
                  <menuitem action="AddAction"/>
                  <menuitem action="RemoveAction"/>
                  <menuitem action="EditAction"/>
                </menu>
                <menu action="ProjectMenu">
                </menu>
                <menu action="DebugMenu">
                  <menuitem action="ShowCommandStack"/>
                  <menuitem action="ShowClipboard"/>
                </menu>
                <menu action="HelpMenu">
                  <menuitem action="About"/>
                </menu>
                </menu>
              </menubar>
              <toolbar name="MainToolbar">
                <toolitem action="Open"/>
                <toolitem action="Save"/>
                <toolitem action="Undo"/>
                <toolitem action="Redo"/>    
              </toolbar>
              <toolbar name="EditBar">
                <toolitem action="Cut"/>
                <toolitem action="Copy"/>
                <toolitem action="Paste"/>
                                <toolitem action="Delete"/>
                              </toolbar>
                            </ui>
                            """
        self._ui_manager = gtk.UIManager()

        action_group = gtk.ActionGroup('MenuActions')
        action_group.add_actions(actions)
        action_group.add_toggle_actions(toggle_actions)
        self._ui_manager.insert_action_group(action_group, 0)

        action_group = gtk.ActionGroup('UndoAction')
        action_group.add_actions(undo_action)
        self._ui_manager.insert_action_group(action_group, 0)
        
        action_group = gtk.ActionGroup('RedoAction')
        action_group.add_actions(redo_action)
        self._ui_manager.insert_action_group(action_group, 0)
        
        self._ui_manager.add_ui_from_string(ui_description)
        
        #application_window.add_accel_group(self._ui_manager.get_accel_group())

        menu = self._ui_manager.get_widget('/MainMenu')


        #toolbarbox = gtk.VBox()
        #mtoolbar = self._ui_manager.get_widget('/MainToolbar')
        #toolbarbox.pack_start(mtoolbar, expand=False)
        #etoolbar = self._ui_manager.get_widget('/EditBar')
        #toolbarbox.pack_start(etoolbar, expand=False)

        #mtoolbar.set_style(gtk.TOOLBAR_ICONS)
        #mtoolbar.set_icon_size(gtk.ICON_SIZE_BUTTON)

        #etoolbar.set_style(gtk.TOOLBAR_ICONS)
        #etoolbar.set_icon_size(gtk.ICON_SIZE_BUTTON)
        
        #print menu, type(menu)
        #bar = gtk.MenuBar()
        
        #parentmenu = gtk.MenuItem(label='Gazpacho')
        #submenu = gtk.Menu()
        #for child in menu.get_children():
        #    menu.remove(child)
        #    print child
        #    submenu.append(child)
        #parentmenu.set_submenu(submenu)
        #bar.append(parentmenu)

        return menu

    def refresh_undo_and_redo(self):
        #return
        undo_item = redo_item = None
        if self._project is not None:
            pri = self._project.prev_redo_item
            if pri != -1:
                undo_item = self._project.undo_stack[pri]
            if pri + 1 < len(self._project.undo_stack):
                redo_item = self._project.undo_stack[pri + 1]

        #undo_action = self._ui_manager.get_action('/MainToolbar/Undo')
        #undo_group = undo_action.get_property('action-group')
        #undo_group.set_sensitive(undo_item is not None)
        self.undo_button.set_sensitive(undo_item is not None)
        undo_widget = self._ui_manager.get_widget('/MainMenu/Gazpacho/EditMenu/Undo')
        label = undo_widget.get_child()
        if undo_item is not None:
            label.set_text_with_mnemonic(('_Undo: %s') % \
                                         undo_item.description)
        else:
            label.set_text_with_mnemonic(('_Undo: Nothing'))
            
        #redo_action = self._ui_manager.get_action('/MainToolbar/Redo')
        #redo_group = redo_action.get_property('action-group')
        #redo_group.set_sensitive(redo_item is not None)
        self.redo_button.set_sensitive(redo_item is not None)
        redo_widget = self._ui_manager.get_widget('/MainMenu/Gazpacho/EditMenu/Redo')
        label = redo_widget.get_child()
        if redo_item is not None:
            label.set_text_with_mnemonic(('_Redo: %s') % \
                                         redo_item.description)
        else:
            label.set_text_with_mnemonic(('_Redo: Nothing'))

        if self._command_stack_window is not None:
            command_stack_view = self._command_stack_window.get_child()
            command_stack_view.update()
 
    def _add_project(self, project):
        # if the project was previously added, don't reload
        for prj in self._projects:
            if prj.path and prj.path == project.path:
                self._set_project(prj)
                return

        self._projects.insert(0, project)

        # add the project in the /Project menu
        project_action= gtk.Action(project.name, project.name, project.name,
                                   '')

        project_action.connect('activate', self._set_project, project)
        project_ui = """
        <ui>
          <menubar name="MainMenu">
            <menu action="Gazpacho">
            <menu action="ProjectMenu">
              <menuitem action="%s"/>
            </menu>
            </menu>
          </menubar>
        </ui>
        """ % project.name
        action_group = self._ui_manager.get_action_groups()[0]
        action_group.add_action(project_action)
        
        project.uim_id = self._ui_manager.add_ui_from_string(project_ui)

        # connect to the project signals so that the editor can be updated
        #project.connect('widget_name_changed', self._widget_name_changed_cb)
        project.connect('project_changed', self._project_changed_cb)
        project.connect('selection_changed',
                         self._project_selection_changed_cb)

        # make sure the palette is sensitive
        self._palette.set_sensitive(True)

        self._set_project(project)

    def _widget_tree_view_create(self):
        from gazpacho.widgettreeview import WidgetTreeView
        view = WidgetTreeView(self)
        self._project_views.insert(0, view)
        view.set_project(self._project)
        #view.set_size_request(150, 200)
        view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        return view

    def _gactions_view_create(self):
        view = GActionsView()
        view.set_project(self._project)
        self._project_views.insert(0, view)
        #view.set_size_request(150, -1)
        view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        return view


    def _command_stack_view_create(self):
        view = CommandStackView()
        self._project_views.insert(0, view)
        view.set_project(self._project)
        #view.set_size_request(300, 200)
        view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        return view

    def _clipboard_view_create(self):
        view = ClipboardView(self._clipboard)
        #view.set_size_request(300, 200)
        view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        return view
 
    def _open_cb(self, action):
        filechooser = gtk.FileChooserDialog(('Open ...'), self.get_window(),
                                            gtk.FILE_CHOOSER_ACTION_OPEN,
                                            (gtk.STOCK_CANCEL,
                                             gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_OPEN,
                                             gtk.RESPONSE_OK))
        file_filter = gtk.FileFilter()
        file_filter.add_pattern("*.glade")
        filechooser.set_filter(file_filter)
        if filechooser.run() == gtk.RESPONSE_OK:
            path = filechooser.get_filename()
            if path:
                self.open_project(path)

        filechooser.destroy()

    def _project_save_as(self, title, project):
        saved = False
        filechooser = gtk.FileChooserDialog(title, self.get_window(),
                                            gtk.FILE_CHOOSER_ACTION_SAVE,
                                            (gtk.STOCK_CANCEL,
                                             gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_SAVE,
                                             gtk.RESPONSE_OK))
        filechooser.set_current_name("%s.glade" % project.name)
        filechooser.set_default_response(gtk.RESPONSE_OK)
        while True:
            if filechooser.run() == gtk.RESPONSE_OK:
                path = filechooser.get_filename()
                if os.path.exists(path):
                    msg = gtk.MessageDialog(parent=self.get_window(),
                                            flags=gtk.DIALOG_MODAL \
                                            | gtk.DIALOG_DESTROY_WITH_PARENT,
                                            type=gtk.MESSAGE_WARNING,
                                            buttons=(gtk.BUTTONS_YES_NO),
                                            message_format=('There is a file with that name already.\nWould you like to overwrite it?'))
                    result = msg.run()
                    msg.destroy()
                    # the user want to overwrite the file
                    if result == gtk.RESPONSE_YES:
                        self._save(project, path)
                        saved = True
                        break

                # the file does not exists. we can save it without worries
                else:
                    self._save(project, path)
                    saved = True
                    break
            # maybe the user changed his/her opinion and don't want to
            # save (by clicking cancel on the file chooser)
            else:
                break
                
        filechooser.destroy()
        return saved

    def _confirm_close_project(self, project):
        submsg1 = ('Save changes to project \"%s\" before closing?') % \
                  project.name
        submsg2 = ("Your changes will be lost if you don't save them")
        msg = "<span weight=\"bold\" size=\"larger\">%s</span>\n\n%s\n" % \
              (submsg1, submsg2)
        dialog = gtk.MessageDialog(self.get_window(), gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE,
                                    msg)
        dialog.label.set_use_markup(True)
        dialog.add_buttons(("Close without Saving"), gtk.RESPONSE_NO,
                            gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                            gtk.STOCK_SAVE, gtk.RESPONSE_YES)
        dialog.set_default_response(gtk.RESPONSE_YES)
        while True:
            ret = dialog.run()
            if ret == gtk.RESPONSE_YES:
                close = True
                if project.path:
                    project.save(project.path)
                    close = True
                else:
                    title = ('Save as')
                    saved = self._project_save_as(title, project)
                    if not saved:
                        continue
            elif ret == gtk.RESPONSE_NO:
                close = True
            else:
                close = False
            break
        dialog.destroy()
        return close


class ExpanderLabel(gtk.HBox):

    def __init__(self, cb, selectorimage):
   
        self.cb = cb
        self.selectorimage = selectorimage
        gtk.HBox.__init__(self)
        
        self.image_holder = gtk.EventBox()
        self.pack_start(self.image_holder, expand=False, padding=4)
        
        self.label = gtk.Label()
        self.pack_start(self.label)

        self.set_label(None)
        

    def _selector_toggled(self, *args):
        pass

    def set_label(self, klass):
        image = self.selectorimage
        text = 'Selector'
        if klass:
            image = klass.icon
            text = klass.name
            #self.selector.set_active(False)
        else:
            pass
            #self.selector.set_active(True)
        
        for child in self.image_holder.get_children():
            self.image_holder.remove(child)

        new_image = get_resized_image_copy(image, 18)
        self.image_holder.add(new_image)
        self.label.set_label(text)
        self.show_all()


def get_resized_image_copy(image, size):
    pb = image.get_pixbuf().scale_simple(size, size, gtk.gdk.INTERP_HYPER)
    new_image = gtk.Image()
    new_image.set_from_pixbuf(pb)
    return new_image
    

class MiniPalette(palette.Palette):
    
    def __init__(self, cb, catalogs):
        self.cb = cb
        self.persistent_mode = True
        gtk.VBox.__init__(self)

        # The GladeWidgetClass corrisponding to the selected button. NULL if
        # the selector button is pressed.
        self._current = None

        #self.pack_start(self._selector_new(), False)
        self._selector_new()
        self.pack_start(gtk.HSeparator(), False, padding=3)

        #The vbox that contains the titles of the sections
        self._groups_vbox = gtk.HBox()
        self.pack_start(self._groups_vbox, False)
        self.pack_start(gtk.HSeparator(), False, padding=3)

        self.groups_combo = gtk.combo_box_new_text()
        self.groups_combo.connect('changed', self.cb_catalog_combo)
        self._groups_vbox.pack_start(self.groups_combo)

        #  Where we store the different catalogs
        self._notebook = gtk.Notebook()
        self._notebook.set_show_tabs(False)
        self._notebook.set_show_border(False)
        self.pack_end(self._notebook)

        # The number of sections in this palette
        self._nb_sections = 0

        # Each section of the palette has a button. This is the
        # sections_button_group list
        self._sections_button_group = []

        for catalog in catalogs:
            for group in catalog.widget_groups:
                self.append_widget_group(group)
        self.groups_combo.set_active(0)

    def append_widget_group(self, group):
        page = self._nb_sections
        self._nb_sections += 1

        # add the button
        #if not self._sections_button_group:
        #    button = gtk.RadioButton(None, group.title.split().pop())
        #else:
        #    button = gtk.RadioButton(self._sections_button_group[0],
                                     #group.title.split().pop())
        #self._sections_button_group = button.get_group()
        #button.set_mode(False)
        #button.set_data('page', page)
        #button.connect('toggled', self._on_catalog_button_toggled)

        #self._groups_vbox.pack_start(button, False)
        self.groups_combo.append_text(group.title)

        # add the selection
        self._notebook.append_page(self._widget_table_create(group),
                                   gtk.Label(''))
        self._notebook.show()
    
    def cb_catalog_combo(self, button):
        page = self.groups_combo.get_active()
        self._notebook.set_current_page(page)
        return True
    
    def _on_button_toggled(self, button, *args):

        if not args and not button.get_active():
            return
        if button == self._selector:
            self._current = None
            self._label.set_text(('Selector'))
        else:
            self._current = button.get_data('user')
            self._label.set_text(self._current.name)

        self.emit('toggled')


    def _widget_table_create(self, group):
        vbox = gtk.VBox()
        rbox = None
        for i, widget_class in enumerate(group):
            if not widget_class.in_palette:
                continue
            
            if i % 5 == 0:
                if rbox:
                    vbox.pack_start(rbox, expand=False)
                rbox = gtk.HBox()
                
            radio = gtk.RadioButton(self._widgets_button_group[0])
            radio.connect('toggled', self._on_button_toggled)
            radio.set_data('user', widget_class)
            radio.set_mode(False)
            radio.set_relief(gtk.RELIEF_NONE)

            self.cb.boss.do_set_tooltip(radio, widget_class.palette_name)

            rbox.pack_start(radio, False, False)
            

            hbox = gtk.HBox(spacing=0)
            image = get_resized_image_copy(widget_class.icon, 20)
            hbox.pack_start(image, False, False)
            radio.add(hbox)

            #label = gtk.Label(widget_class.palette_name)
            #label.set_alignment(0.0, 0.5)
            #hbox.pack_start(label, padding=1)

            self._widgets_button_group = radio.get_group()

        vbox.pack_start(rbox, expand=False)
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        #scrolled_window.add_with_viewport(vbox)
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_size_request(-1, 200)

        return vbox

    def _selector_new(self):
        hbox = gtk.HBox()
        # The selector is a button that is clicked to cancel the add widget
        # action. This sets our cursor back to the "select widget" mode. This
        # button is part of the widgets_button_group, so that when no widget
        # is selected, this button is pressed.
        self._selector = gtk.RadioButton(None)
        self._selector.set_mode(False)
        self._selector.set_relief(gtk.RELIEF_NONE)
        
        # Each widget in a section has a button in the palette. This is the
        # button group, since only one may be pressed.
        self._widgets_button_group = self._selector.get_group()

        image = gtk.Image()
        image.set_from_file(os.path.join(pixmaps_dir, 'selector.png'))
        image = get_resized_image_copy(image, 18)
        self._selector.add(image)
        self._selector.connect('toggled', self._on_button_toggled)

        # A label which contains the name of the class currently selected or
        # "Selector" if no widget class is selected
        self._label = gtk.Label(('Selector'))
        self._label.set_alignment(0.0, 0.5)

        #hbox.pack_start(self._selector, False, False)
        #hbox.pack_start(self._label, padding=2)
        #hbox.show_all()

        return self._selector


