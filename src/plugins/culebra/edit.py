# -*- coding: utf-8 -*-
# Copyright Fernando San Martín Woerner <fsmw@gnome.org>
# $Id: edit.py 475 2005-07-29 17:29:32Z snmartin $
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# This file is part of Culebra project.

import gtk
import sys, os
import pango
import dialogs
import gtksourceview
import gnomevfs
import importsTipper
import keyword

BLOCK_SIZE = 2048

special_chars = (".",)
RESPONSE_FORWARD = 0
RESPONSE_BACKWARD = 1
RESPONSE_REPLACE = 2
RESPONSE_REPLACE_ALL = 3

global newnumber
newnumber = 1

class CulebraBuffer(gtksourceview.SourceBuffer):

    def __init__(self, filename=None):
        gtksourceview.SourceBuffer.__init__(self)
        self.filename=filename


class CulebraView(gtksourceview.SourceView):

    def __init__(self, buff=CulebraBuffer()):
        if buffer is None:
            gtksourceview.SourceView.__init__(self)
        else:
            gtksourceview.SourceView.__init__(self, buff)
                
class EditWindow(gtk.EventBox):

    def __init__(self, plugin=None, quit_cb=None):
        gtk.EventBox.__init__(self)
        self.search_string = None
        self.last_search_iter = None
        self.completion_win = None
        self.insert_string = None
        self.cursor_iter = None
        self.plugin = plugin
        self.wins = []
        self.current_word = ""
        self.wl = []
        self.ac_w = None
        self.set_size_request(470, 300)
        self.connect("delete_event", self.file_exit)
        self.quit_cb = quit_cb
        self.vbox = gtk.VBox()
        self.add(self.vbox)
        self.vbox.show()
        self.menubar, self.toolbar = self.create_menu()
        hdlbox = gtk.HandleBox()
        self.vbox.pack_start(hdlbox, expand=False)
        hdlbox.show()
        hdlbox.add(self.menubar)
        self.menubar.show()
        hdlbox = gtk.HandleBox()
        self.vbox.pack_start(hdlbox, expand=False)
        hdlbox.show()
        hdlbox.add(self.toolbar)
        self.toolbar.show()
        self.vpaned = gtk.VPaned()
        self.vbox.pack_start(self.vpaned, expand=True, fill = True)
        self.vpaned.show()
        self.vbox1 = gtk.VBox()
        self.vpaned.add1(self.vbox1)
        self.vbox.show()
        self.vbox1.show()
        self.hpaned = gtk.HPaned()
        self.vbox1.pack_start(self.hpaned, True, True)
        self.hpaned.set_border_width(5)
        self.hpaned.show()
        # the gtksourceview
        lm = gtksourceview.SourceLanguagesManager()
        buff = CulebraBuffer()
        self.new = True
        buff.set_data('languages-manager', lm)
#        self.editor = gtksourceview.SourceView(buff)
        self.editor = CulebraView(buff)
        self.plugin.pida.mainwindow.connect('delete-event', self.file_exit)
        font_desc = pango.FontDescription('monospace 10')
        if font_desc:
            self.editor.modify_font(font_desc)
        
        buff.connect('insert-text', self.insert_at_cursor_cb)
        buff.set_data("save", False)
        manager = buff.get_data('languages-manager')
        language = manager.get_language_from_mime_type("text/x-python")
        buff.set_highlight(True)
        buff.set_language(language)
        scrolledwin2 = gtk.ScrolledWindow()
        scrolledwin2.add(self.editor)
        self.editor.set_auto_indent(True)
        self.editor.set_show_line_numbers(True)
        self.editor.set_show_line_markers(True)
        self.editor.set_tabs_width(4)
        self.editor.connect('key-press-event', self.text_key_press_event_cb)
        self.editor.connect('move-cursor', self.move_cursor)
        self.editor.set_margin(80)
        self.editor.set_show_margin(True)
        self.editor.set_smart_home_end(True)
        self.editor.set_highlight_current_line(True)
        scrolledwin2.show()
        self.editor.show()
        self.editor.grab_focus()
        buff.set_data('filename', "untitled.py")
        self.wins.append([buff, "untitled.py"])
        self.current_buffer = 0
        self.hpaned.add2(scrolledwin2)
        self.hpaned.set_position(200)
        self.dirty = 0
        self.clipboard = gtk.Clipboard(selection='CLIPBOARD')
        self.dirname = "."
        # sorry, ugly
        self.filetypes = {}
        return
        
    def create_menu(self):
        ui_string = """<ui>
        <menubar>
                <menu name='FileMenu' action='FileMenu'>
                        <menuitem action='FileNew'/>
                        <menuitem action='FileOpen'/>
                        <menuitem action='FileSave'/>
                        <menuitem action='FileSaveAs'/>
                        <menuitem action='Close'/>
                        <separator/>
                        <menuitem action='FileExit'/>
                </menu>
                <menu name='EditMenu' action='EditMenu'>
                        <menuitem action='EditUndo'/>
                        <menuitem action='EditRedo'/>
                        <separator/>
                        <menuitem action='EditCut'/>
                        <menuitem action='EditCopy'/>
                        <menuitem action='EditPaste'/>
                        <menuitem action='EditClear'/>
                        <separator/>
                        <menuitem action='DuplicateLine'/>
                        <menuitem action='DeleteLine'/>
                        <menuitem action='CommentBlock'/>
                        <menuitem action='UncommentBlock'/>
                        <menuitem action='UpperSelection'/>
                        <menuitem action='LowerSelection'/>
                        <separator/>
                        <menuitem action='Configuration' />
                </menu>
                <menu name='FindMenu' action='FindMenu'>
                        <menuitem action='EditFind'/>
                        <menuitem action='EditFindNext'/>
                        <menuitem action='EditReplace'/>
                        <separator/>                        
                        <menuitem action='GotoLine'/>
                </menu>
                <menu name='RunMenu' action='RunMenu'>
                        <menuitem action='RunScript'/>
                        <menuitem action='StopScript'/>
                        <menuitem action='DebugScript'/>
                        <menuitem action='DebugStep'/>
                        <menuitem action='DebugNext'/>
                        <menuitem action='DebugContinue'/>
                </menu>
                <menu name='BufferMenu' action='BufferMenu'>
                        <menuitem action='PrevBuffer'/>
                        <menuitem action='NextBuffer'/>
                </menu>
        </menubar>
        <toolbar>
                <toolitem action='FileNew'/>
                <toolitem action='FileOpen'/>
                <toolitem action='FileSave'/>
                <toolitem action='FileSaveAs'/>
                <toolitem action='Close'/>
                <separator/>
                <toolitem action='EditUndo'/>
                <toolitem action='EditRedo'/>
                <separator/>
                <toolitem action='EditCut'/>
                <toolitem action='EditCopy'/>
                <toolitem action='EditPaste'/>
                <separator/>
                <toolitem action='EditFind'/>
                <toolitem action='EditReplace'/>
                <separator/>
                <toolitem action='RunScript'/>
                <toolitem action='StopScript'/>
                <separator/>
                <toolitem action='PrevBuffer'/>
                <toolitem action='NextBuffer'/>
        </toolbar>
        </ui>
        """
        actions = [
            ('FileMenu', None, '_File'),
            ('FileNew', gtk.STOCK_NEW, None, None, None, self.file_new),
            ('FileOpen', gtk.STOCK_OPEN, None, None, None, self.file_open),
            ('FileSave', gtk.STOCK_SAVE, None, None, None, self.file_save),
            ('FileSaveAs', gtk.STOCK_SAVE_AS, None, None, None,
             self.file_saveas),
            ('Close', gtk.STOCK_CLOSE, None, None, None, self.file_close),
            ('FileExit', gtk.STOCK_QUIT, None, None, None, self.file_exit),
            ('EditMenu', None, '_Edit'),
            ('EditUndo', gtk.STOCK_UNDO, None, "<control>z", None, self.edit_undo),
            ('EditRedo', gtk.STOCK_REDO, None, "<control><shift>z", None, self.edit_redo),
            ('EditCut', gtk.STOCK_CUT, None, None, None, self.edit_cut),
            ('EditCopy', gtk.STOCK_COPY, None, None, None, self.edit_copy),
            ('EditPaste', gtk.STOCK_PASTE, None, None, None, self.edit_paste),
            ('EditClear', gtk.STOCK_REMOVE, 'C_lear', None, None,
             self.edit_clear),
            ('Configuration', None, 'Configur_e', None, None,
                lambda action: self.plugin.do_action('showconfig', 'culebra')),
            
             ('DuplicateLine', None, 'Duplicate Line', '<control>d', 
                 None, self.duplicate_line),
             ('DeleteLine', None, 'Delete Line', '<control>y', 
                 None, self.delete_line),
             ('CommentBlock', None, 'Comment Selection', '<control>k', 
                 None, self.comment_block),
             ('UncommentBlock', None, 'Uncomment Selection', '<control><shift>k', 
                 None, self.uncomment_block),
             ('UpperSelection', None, 'Upper Selection', '<control>u', 
                 None, self.upper_selection),
             ('LowerSelection', None, 'Lower Selection', '<control><shift>u', 
                 None, self.lower_selection),
            ('FindMenu', None, '_Find'),
            ('EditFind', gtk.STOCK_FIND, None, None, None, self.edit_find),
            ('EditFindNext', None, 'Find _Next', None, None, self.edit_find_next),
            ('EditReplace', gtk.STOCK_FIND_AND_REPLACE, None, '<control>h', 
                None, self.edit_replace),
            ('GotoLine', None, 'Goto Line', '<control>g', 
                 None, self.goto_line),
            ('RunMenu', None, '_Run'),
            ('RunScript', gtk.STOCK_EXECUTE, None, "F5",None, self.run_script),
            ('StopScript', gtk.STOCK_STOP, None, "<ctrl>F5",None, self.stop_script),
            ('DebugScript', None, "Debug Script", "F7",None, self.debug_script),
            ('DebugStep', None, "Step", "F8",None, self.step_script),
            ('DebugNext', None, "Next", "<shift>F7",None, self.next_script),
            ('DebugContinue', None, "Continue", "<control>F7", None, self.continue_script),
            ('BufferMenu', None, '_Buffers'),
            ('PrevBuffer', gtk.STOCK_GO_UP, None, "<shift>F6",None, self.prev_buffer),
            ('NextBuffer', gtk.STOCK_GO_DOWN, None, "F6",None, self.next_buffer),
            ]
        self.ag = gtk.ActionGroup('edit')
        self.ag.add_actions(actions)
        self.ui = gtk.UIManager()
        self.ui.insert_action_group(self.ag, 0)
        self.ui.add_ui_from_string(ui_string)
        self.get_parent_window().add_accel_group(self.ui.get_accel_group())
        return (self.ui.get_widget('/menubar'), self.ui.get_widget('/toolbar'))
    
    def set_title(self, title):
        self.plugin.pida.mainwindow.set_title(title)

    def move_cursor(self, tv, step, count, extend_selection):
        return

    def get_parent_window(self):
        return self.plugin.pida.mainwindow

    def get_current(self, page = None):
        if len(self.wins) > 0:
            if page is None:
                return self.wins[self.current_buffer]
        return None, None

    def _new_tab(self, f, buff = None):
        l = [n for n in self.wins if n[1]==f]
        if len(l) == 0:
            lm = gtksourceview.SourceLanguagesManager()
            if buff is None:
                buff = CulebraBuffer()
                self.new = True
            buff.set_data('languages-manager', lm)
            font_desc = pango.FontDescription('monospace 10')
            if font_desc:
                self.editor.modify_font(font_desc)
            buff.connect('insert-text', self.insert_at_cursor_cb)
            buff.set_data("save", False)
            self.editor.set_buffer(buff)
            self.editor.grab_focus()
            buff.set_data('filename', f)
            self.wins.append([buff, f])
            self.current_buffer = len(self.wins) - 1

    def insert_at_cursor_cb(self, buff, iter, text, length):
        complete = ""
        buff, fn = self.get_current()
        iter2 = buff.get_iter_at_mark(buff.get_insert())
        s, e = buff.get_bounds()
        text_code = buff.get_text(s, e)
        lst_ = []
        if self.ac_w is not None:
            self.ac_w.hide()
        mod = False
        if text != '.':
            complete = self.get_context(buff, iter2, True)
            if "\n" in complete or complete.isdigit():
                return
            else:
                complete = complete + text
            try:
                c = compile(text_code, '<string>', 'exec')
                lst_ = [a for a in c.co_names if a.startswith(complete)]
                con = map(str, c.co_consts)
                con = [a for a in con if a.startswith(complete) and a not in lst_]
                lst_ += con
                lst_ += keyword.kwlist
                lst_ = [a for a in lst_ if a.startswith(complete)]
                lst_.sort()
            except:
                lst_ += keyword.kwlist
                lst_ = [a for a in lst_ if a.startswith(complete)]
                lst_.sort()
        else:
            mod = True
            complete = self.get_context(buff, iter2)
            if complete.isdigit():
                return
            if len(complete.strip()) > 0:
                try:
                    lst_ = [str(a[0]) for a in importsTipper.GenerateTip(complete, os.path.dirname(fn)) if a is not None]
                except:
                    try:
                        c = compile(text_code, '<string>', 'exec')
                        lst_ = [a for a in c.co_names if a.startswith(complete)]
                        con = map(str, c.co_consts)
                        con = [a for a in con if a.startswith(complete) and a not in lst_]
                        lst_ += con
                        lst_ += keyword.kwlist
                        lst_ = [a for a in lst_ if a.startswith(complete)]
                        lst_.sort()
                        complete = ""
                    except:
                        lst_ += keyword.kwlist
                        lst_ = [a for a in lst_ if a.startswith(complete)]
                        lst_.sort()
                        complete = ""
                        
        if len(lst_)==0:
            return
        if self.ac_w is None:
            self.ac_w = AutoCompletionWindow(self.editor, iter2, complete, 
                                        lst_, 
                                        self.plugin.pida.mainwindow, 
                                        mod, 
                                        self.context_bounds)
        else:
            self.ac_w.set_list(self.editor, iter2, complete, 
                           lst_, 
                           self.plugin.pida.mainwindow, 
                           mod, 
                           self.context_bounds)
        return
        
    def get_context(self, buff, it, sp=False):
        iter2 = it.copy()
        if sp:
            it.backward_word_start()
        else:
            it.backward_word_starts(1)
        iter3 = it.copy()
        iter3.backward_chars(1)
        prev = iter3.get_text(it)
        complete = it.get_text(iter2)
        self.context_bounds = (buff.create_mark('cstart',it), buff.create_mark('cend',iter2))
        if prev in (".", "_"):
            t = self.get_context(buff, it)
            return t + complete
        else:
            count = 0
            return complete

    def text_key_press_event_cb(self, widget, event):
        #print event.state, event.keyval
        keyname = gtk.gdk.keyval_name(event.keyval)
        buf = widget.get_buffer()
        bound = buf.get_selection_bounds()
        tabs = widget.get_tabs_width()
        space = " ".center(tabs)
        # shift-tab unindent
        if event.state & gtk.gdk.SHIFT_MASK and keyname == "ISO_Left_Tab":
            if len(bound) == 0:
                it = buf.get_iter_at_mark(buf.get_insert())
                start = buf.get_iter_at_line(it.get_line())
                end = buf.get_iter_at_line(it.get_line())
                count = 0
                while end.get_char() == " " and count < tabs:
                    end.forward_char()
                    count += 1
                buf.delete(start, end)
            else:
                start, end = bound
                start_line = start.get_line()
                end_line = end.get_line()
                while start_line <= end_line:
                    insert_iter = buf.get_iter_at_line(start_line)
                    if not insert_iter.ends_line():
                        s_it = buf.get_iter_at_line(start_line)
                        e_it = buf.get_iter_at_line(start_line)
                        count = 0
                        while e_it.get_char() == " " and count < tabs:
                            e_it.forward_char()
                            count += 1
                        buf.delete(s_it, e_it)        
                    start_line += 1
            return True
        #tab indent
        elif event.keyval == gtk.keysyms.Tab:
            if len(bound) == 0:
                buf.insert_at_cursor(space)
            else:
                start, end = bound
                start_line = start.get_line()
                end_line = end.get_line()
                while start_line <= end_line:
                    insert_iter = buf.get_iter_at_line(start_line)
                    if not insert_iter.ends_line():
                        buf.insert(insert_iter, space)
                    start_line += 1
            return True

    def load_file(self, fname):
        try:
            fd = open(fname)
            self._new_tab(fname)
            buff, fn = self.wins[self.current_buffer]
            buff.set_text('')
            buff.set_data('filename', fname)
            buff.set_text(fd.read())
            fd.close()
            self.editor.set_buffer(buff)
            self.editor.queue_draw()
            self.set_title(os.path.basename(fname))
            self.dirname = os.path.dirname(fname)
            buff.set_modified(False)
            self.new = False
            self.check_mime(self.current_buffer)
            buff.place_cursor(buff.get_start_iter())
        except:
            dlg = gtk.MessageDialog(self.get_parent_window(),
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    "Can't open " + fname)
            print sys.exc_info()[1]
            resp = dlg.run()
            dlg.hide()
            return
        self.check_mime(self.current_buffer)
        self.plugin.do_edit('getbufferlist')
        self.plugin.do_edit('getcurrentbuffer')
        for i, (buff, fn) in enumerate(self.wins):
            if fn == fname:
                self.plugin.do_edit('changebuffer', i)
                break
        self.editor.grab_focus()

    def check_mime(self, buffer_number):
        buff, fname = self.wins[buffer_number]
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
                buff.set_highlight(True)
                buff.set_language(language)
            else:
                dlg = gtk.MessageDialog(self.get_parent_window(),
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    'No language found for mime type "%s"' % mime_type)
                buff.set_highlight(False)
        else:
            dlg = gtk.MessageDialog(self.get_parent_window(),
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    'Couldn\'t get mime type for file "%s"' % fname)
            buff.set_highlight(False)
        buff.set_data("save", False)

    def chk_save(self):
        buff, fname = self.get_current()
        if buff is None:
            return False
        if buff.get_modified():
            dlg = gtk.Dialog('Unsaved File', self.get_parent_window(),
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                         (gtk.STOCK_YES, gtk.RESPONSE_YES,
                          gtk.STOCK_NO, gtk.RESPONSE_NO,
                          gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
            lbl = gtk.Label((fname or "Untitled")+
                        " has not been saved\n" +
                        "Do you want to save it?")
            lbl.show()
            dlg.vbox.pack_start(lbl)
            ret = dlg.run()
            dlg.hide()
            if ret == gtk.RESPONSE_NO:
                return False
            if ret == gtk.RESPONSE_YES:
                if self.file_save():
                    return False
            return True
        return False

    def file_new(self, mi=None):
        if self.chk_save(): return
        self._new_tab("untitled%s.py" % len(self.wins))
        buff, fname = self.get_current()
        buff.set_text("")
        buff.set_data('filename', fname)
        buff.set_modified(False)
        self.new = True
        manager = buff.get_data('languages-manager')
        language = manager.get_language_from_mime_type("text/x-python")
        buff.set_highlight(True)
        buff.set_language(language)
        self.plugin.do_edit('getbufferlist')
        self.plugin.do_edit('getcurrentbuffer')
        self.plugin.do_edit('changebuffer', len(self.wins) - 1)

        return

    def file_open(self, mi=None):
        fn = self.get_current()[1]
        dirn =os.path.dirname(fn)
        fname = dialogs.OpenFile('Open File', self.get_parent_window(),
                                  dirn, None, "*.py")
        
        if not fname: return
        if self.new:
            buff = self.get_current()[0]
            if not buff.get_modified():
                del self.wins[self.current_buffer]
        self.load_file(fname)
        self.plugin.pida.mainwindow.set_title(os.path.split(fname)[1])
        return

    def file_save(self, mi=None, fname=None):
        if self.new:
            return self.file_saveas()
        buff = self.editor.get_buffer()
        curr_mark = buff.get_iter_at_mark(buff.get_insert())
        f = buff.get_data('filename')
        ret = False
        if fname is None:
            fname = f
        try:
            start, end = buff.get_bounds()
            blockend = start.copy()
            fd = open(fname, "w")
            while blockend.forward_chars(BLOCK_SIZE):
                buf = buff.get_text(start, blockend)
                fd.write(buf)
                start = blockend.copy()
            buf = buff.get_text(start, blockend)
            fd.write(buf)
            fd.close()
            buff.set_modified(False)
            buff.set_data("save", True)
            buff.set_data('filename', fname)
            self.plugin.pida.mainwindow.set_title(os.path.split(fname)[1])
            ret = True
            self.wins[self.current_buffer] = [buff, fname]
        except:
            dlg = gtk.MessageDialog(self.get_parent_window(),
                                gtk.DIALOG_DESTROY_WITH_PARENT,
                                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                "Error saving file " + fname)
            print sys.exc_info()[1]
            resp = dlg.run()
            dlg.hide()

        self.check_mime(self.current_buffer)
        self.plugin.do_edit('getbufferlist')
        self.plugin.do_edit('getcurrentbuffer')
#        self.plugin.do_edit('changebuffer', len(self.wins) - 1)
        buff.place_cursor(curr_mark)
        self.editor.grab_focus()
        return ret

    def file_saveas(self, mi=None):
        buff, f = self.get_current()
        f = dialogs.SaveFile('Save File As', 
                                self.get_parent_window(), 
                                self.dirname,
                                f)
        if not f: return False

        self.dirname = os.path.dirname(f)
        self.plugin.pida.mainwindow.set_title(os.path.basename(f))
        self.new = 0
        return self.file_save(fname=f)

    def file_close(self, mi=None, event=None):
        del self.wins[self.current_buffer]
        if len(self.wins) == 0:
            self._new_tab('untitled.py')
        else:
            self.current_buffer = len(self.wins) - 1
            self.editor.set_buffer(self.wins[self.current_buffer][0])
        self.plugin.do_edit('getbufferlist')
        self.plugin.do_edit('getcurrentbuffer')
        return

    def file_exit(self, mi=None, event=None):
        if self.chk_save(): return True
        self.hide()
        self.destroy()
        if self.quit_cb: self.quit_cb(self)
        self.plugin.do_action('quit')
        return False

    def edit_cut(self, mi):
        buff = self.get_current()[0]
        buff.cut_clipboard(self.clipboard, True)
        return

    def edit_copy(self, mi):
        buff = self.get_current()[0]
        buff.copy_clipboard(self.clipboard)
        return

    def edit_paste(self, mi):
        buff = self.get_current()[0]
        buff.paste_clipboard(self.clipboard, None, True)
        return

    def edit_clear(self, mi):
        buff = self.get_current()[0]
        buff.delete_selection(True, True)
        return
        
    def edit_undo(self, mi):
        buff = self.get_current()[0]
        buff.undo()
        
    def edit_redo(self, mi):
        buff = self.get_current()[0]
        buff.redo()

    def edit_find(self, mi): 
        def dialog_response_callback(dialog, response_id):
            if response_id == gtk.RESPONSE_CLOSE:
                dialog.destroy()
                return
            self._search(search_text.get_text(), self.last_search_iter)
        buff = self.get_current()[0]
        search_text = gtk.Entry()
        s = buff.get_selection_bounds()
        if len(s) > 0:
            search_text.set_text(buff.get_slice(s[0], s[1]))
        dialog = gtk.Dialog("Search", self.get_parent_window(),
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_FIND, RESPONSE_FORWARD,
                             gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        dialog.vbox.pack_end(search_text, True, True, 0)
        dialog.connect("response", dialog_response_callback)
        dialog.set_default_response(RESPONSE_FORWARD)
        search_text.set_activates_default(True)
        search_text.show()
        search_text.grab_focus()
        dialog.show_all()
        response_id = dialog.run()
        
    def edit_replace(self, mi): 
        def dialog_response_callback(dialog, response_id):
            if response_id == gtk.RESPONSE_CLOSE:
                dialog.destroy()
                return
            if response_id == RESPONSE_FORWARD:
                self._search(search_text.get_text(), self.last_search_iter)
                return
            if response_id == RESPONSE_REPLACE:
                if not self._search(search_text.get_text(), self.last_search_iter):
                    return
                start, end = buff.get_selection_bounds()
                buff.delete(start, end)
                buff.insert(start, replace_text.get_text())
                self.last_search_iter = buff.get_iter_at_mark(buff.get_insert())
                start = buff.get_iter_at_mark(buff.get_insert())
                start.backward_chars(len(replace_text.get_text()))
                buff.select_range(start, self.last_search_iter)
            if response_id == RESPONSE_REPLACE_ALL:
                current_iter = buff.get_iter_at_mark(buff.get_insert())
                while self._search(search_text.get_text(), self.last_search_iter, False):
                    start, end = buff.get_selection_bounds()
                    buff.delete(start, end)
                    buff.insert(start, replace_text.get_text())
                    self.last_search_iter = buff.get_iter_at_mark(buff.get_insert())
                    start = buff.get_iter_at_mark(buff.get_insert())
                    start.backward_chars(len(replace_text.get_text()))
                    buff.select_range(start, self.last_search_iter)
                buff.place_cursor(current_iter)
        buff = self.get_current()[0]
        search_text = gtk.Entry()
        replace_text = gtk.Entry() 
        s = buff.get_selection_bounds()
        if len(s) > 0:
            search_text.set_text(buff.get_slice(s[0], s[1]))
        dialog = gtk.Dialog("Search", self.get_parent_window(),
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_FIND, RESPONSE_FORWARD,
                             "Replace", RESPONSE_REPLACE,
                             "Replace All", RESPONSE_REPLACE_ALL,
                             gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        lbl = gtk.Label("Find what:")
        dialog.vbox.pack_start(lbl, True, True, 0)
        dialog.vbox.pack_start(search_text, True, True, 0)
        lbl = gtk.Label("Replace with:")
        dialog.vbox.pack_start(lbl, True, True, 0)
        dialog.vbox.pack_start(replace_text, True, True, 0)
        dialog.connect("response", dialog_response_callback)
        dialog.set_default_response(RESPONSE_FORWARD)
        search_text.set_activates_default(True)
        replace_text.set_activates_default(True)
        search_text.show()
        replace_text.show()
        search_text.grab_focus()
        dialog.show_all()
        response_id = dialog.run()
    
    def _search(self, search_string, iter = None, scroll=True):
        buff, fname = self.get_current()
        if iter is None:
            start = buff.get_start_iter()
        else:
            start = iter
        i = 0
        if search_string:
            self.search_string = search_string
            res = start.forward_search(search_string, gtk.TEXT_SEARCH_TEXT_ONLY)
            if res:
                match_start, match_end = res
                buff.place_cursor(match_start)
                buff.select_range(match_start, match_end)
                if scroll:
                    self.editor.scroll_to_iter(match_start, 0.25)
                self.last_search_iter = match_end
                return True
            else:
                self.search_string = None
                self.last_search_iter = buff.get_iter_at_mark(buff.get_insert())
                return False
            
    def edit_find_next(self, mi):
        self._search(self.search_string, self.last_search_iter)
    
    def goto_line(self, mi=None):
        def dialog_response_callback(dialog, response_id):
            if response_id == gtk.RESPONSE_CLOSE:
                dialog.destroy()
                return
            line = line_text.get_text()
            if line.isdigit():
                buff, f = self.get_current()
                titer = buff.get_iter_at_line(int(line)-1)
                self.editor.scroll_to_iter(titer, 0.25)
                buff.place_cursor(titer)
                self.editor.grab_focus()
                dialog.destroy()
       
        line_text = gtk.Entry()
        dialog = gtk.Dialog("Goto Line", self.get_parent_window(),
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_GO_FORWARD, RESPONSE_FORWARD,
                             gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        dialog.vbox.pack_end(line_text, True, True, 0)
        dialog.connect("response", dialog_response_callback)
        dialog.set_default_response(RESPONSE_FORWARD)
        line_text.set_activates_default(True)
        line_text.show()
        line_text.grab_focus()
        dialog.show_all()
        response_id = dialog.run()

    def comment_block(self, mi=None):
        comment = "#"
        buf = self.get_current()[0]
        bound = buf.get_selection_bounds()
        if len(bound) == 0:
            it = buf.get_iter_at_mark(buf.get_insert())
            line = it.get_line()
            insert_iter = buf.get_iter_at_line(line)
            buf.insert(insert_iter, comment)
        else:
            start, end = bound
            start_line = start.get_line()
            end_line = end.get_line()
            while start_line <= end_line:
                insert_iter = buf.get_iter_at_line(start_line)
                if not insert_iter.ends_line():
                    buf.insert(insert_iter, comment)
                start_line += 1
   
    def uncomment_block(self, mi=None):
        buf = self.get_current()[0]
        bound = buf.get_selection_bounds()
        if len(bound) == 0:
            it = buf.get_iter_at_mark(buf.get_insert())
            start = buf.get_iter_at_line(it.get_line())
            end = buf.get_iter_at_line(it.get_line())
            count = 0
            while end.get_char() == "#":
                end.forward_char()
                count += 1
            buf.delete(start, end)
        else:
            start, end = bound
            start_line = start.get_line()
            end_line = end.get_line()
            while start_line <= end_line:
                insert_iter = buf.get_iter_at_line(start_line)
                if not insert_iter.ends_line():
                    s_it = buf.get_iter_at_line(start_line)
                    e_it = buf.get_iter_at_line(start_line)
                    count = 0
                    while e_it.get_char() == "#":
                        e_it.forward_char()
                        count += 1
                    buf.delete(s_it, e_it)        
                start_line += 1
                
    def delete_line(self, mi):
        buf = self.get_current()[0]
        it = buf.get_iter_at_mark(buf.get_insert())
        line = it.get_line()
        start = buf.get_iter_at_line(line)
        end = buf.get_iter_at_line(line+1)
        if start.get_line() == end.get_line():
            end.forward_to_end()
        buf.delete(start, end)
            
    def duplicate_line(self, mi):
        buf = self.get_current()[0]
        it = buf.get_iter_at_mark(buf.get_insert())
        line = it.get_line()
        start = buf.get_iter_at_line(line)
        end = buf.get_iter_at_line(line+1)
        ret = ""
        if start.get_line() == end.get_line():
            end.forward_to_end()
            ret = "\n"
        text = buf.get_text(start, end)
        buf.insert(end, ret+text)
    
    def upper_selection(self, mi):
        buf = self.get_current()[0]
        bound = buf.get_selection_bounds()
        if not len(bound) == 0:
            start, end = bound
            text = buf.get_text(start, end)
            buf.delete(start, end)
            buf.insert(start, text.upper())
            
    def lower_selection(self, mi):
        buf = self.get_current()[0]
        bound = buf.get_selection_bounds()
        if not len(bound) == 0:
            start, end = bound
            text = buf.get_text(start, end)
            buf.delete(start, end)
            buf.insert(start, text.lower())
    
    def run_script(self, mi):
        self.file_save()
        self.plugin.do_evt("bufferexecute") 
        
    def stop_script(self, mi):
        self.plugin.do_evt('killterminal')
        
    def debug_script(self, mi):
        self.plugin.do_evt('debuggerload')
        buff = self.get_current()[0]
        titer = buff.get_iter_at_line(0)
        self.editor.scroll_to_iter(titer, 0.25)
        buff.place_cursor(titer)
        
    def step_script(self, mi):
        self.plugin.do_evt('step')

    def next_script(self, mi):
        self.plugin.do_evt('next')

    def continue_script(self, mi):
        self.plugin.do_evt('continue')
        
    def next_buffer(self, mi):
        i = self.current_buffer + 1
        if i >= len(self.wins):
            i = 0
        self.plugin.do_edit('changebuffer', i)

    def prev_buffer(self, mi):
        i = self.current_buffer - 1
        if i < 0:
            i = len(self.wins) - 1
        self.plugin.do_edit('changebuffer', i)

        
class AutoCompletionWindow(gtk.Window):
    
    def __init__(self,  source_view, trig_iter, text, lst, parent, mod, cbound):
        
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        self.set_decorated(False)
        self.store = gtk.ListStore(str, str, str)
        self.source = source_view
        self.it = trig_iter
        self.mod = mod
        self.cbounds = cbound
        self.found = False
        self.text = text
        frame = gtk.Frame()
        
        for i in lst:
            self.store.append((gtk.STOCK_CONVERT, i, ""))
        self.tree = gtk.TreeView(self.store)
        
        render = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn('', render, stock_id=0)
        self.tree.append_column(column)
        col = gtk.TreeViewColumn()
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn('', render, text=1)
        self.tree.append_column(column)
        col = gtk.TreeViewColumn()
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn('', render, text=2)
        self.tree.append_column(column)
        rect = source_view.get_iter_location(trig_iter)
        wx, wy = source_view.buffer_to_window_coords(gtk.TEXT_WINDOW_WIDGET, 
                                rect.x, rect.y + rect.height)

        tx, ty = source_view.get_window(gtk.TEXT_WINDOW_WIDGET).get_origin()
        wth, hht = parent.get_size()
        width = wth - (tx+wx)
        height = hht - (ty+wy)
        if width > 200: width = 200
        if height > 200: height = 200
        self.move(wx+tx, wy+ty)
        self.add(frame)
        frame.add(self.tree)
        self.tree.set_size_request(width, height)
        self.tree.connect('row-activated', self.row_activated_cb)
        self.tree.connect('focus-out-event', self.focus_out_event_cb)
        self.tree.connect('key-press-event', self.key_press_event_cb)
        self.tree.set_search_column(1)
        self.tree.set_search_equal_func(self.search_func)
        self.tree.set_headers_visible(False)
        self.set_transient_for(parent)
        self.show_all()
        self.tree.set_cursor((0,))
        self.tree.grab_focus()
        
    def set_list(self, source_view, trig_iter, text, lst, parent, mod, cbound):
        self.mod = mod
        self.cbounds = cbound
        self.store = gtk.ListStore(str, str, str)
        self.source = source_view
        self.it = trig_iter
        self.found = False
        self.text = text
        for i in lst:
            self.store.append((gtk.STOCK_CONVERT, i, ""))
        self.tree.set_model(self.store)
        self.tree.set_search_column(1)
        self.tree.set_search_equal_func(self.search_func)
        rect = source_view.get_iter_location(trig_iter)
        wx, wy = source_view.buffer_to_window_coords(gtk.TEXT_WINDOW_WIDGET, 
                                rect.x, rect.y + rect.height)
        tx, ty = source_view.get_window(gtk.TEXT_WINDOW_WIDGET).get_origin()
        wth, hht = parent.get_size()
        wth += tx
        hht += ty
        width = wth - (wx+tx) 
        height = hht - (wy+ty)
        if width > 200: width = 200
        if height > 200: height = 200
        self.move(wx+tx, wy+ty)
        self.tree.set_size_request(width, height)
        self.show_all()
        self.tree.set_cursor((0,))
        self.tree.grab_focus()
        
    def row_activated_cb(self, tree, path, view_column, data = None):
        self.complete = self.store[path][1] + self.store[path][2]
        self.insert_complete()
        
    def insert_complete(self):
        buff = self.source.get_buffer()
        try:
            if not self.mod:
                s, e = self.cbounds
                buff.select_range(buff.get_iter_at_mark(s), buff.get_iter_at_mark(e))
                start, end = buff.get_selection_bounds()
                buff.delete(start, end)
                buff.insert(start, self.complete)
            else:
                buff.insert_at_cursor(self.complete)
        except:
            buff.insert_at_cursor(self.complete[len(self.text):])
        self.hide()

    def focus_out_event_cb(self, widget, event):
        self.hide()

    def key_press_event_cb(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.hide()
        elif event.keyval == gtk.keysyms.BackSpace:
            self.hide()
            
    def search_func(self, model, column, key, it):
        if self.mod:
            cp_text = key
        else:
            cp_text = self.text + key
            self.complete = cp_text
        if model.get_path(model.get_iter_first()) == model.get_path(it):
            self.found = False
        if model.get_value(it, column).startswith(cp_text):
            self.found = True
        if model.iter_next(it) is None and not self.found:
            if self.text != "":
                self.complete = model.get_value(it, 1)
            else:
                self.complete = key
            self.insert_complete()
            self.hide()
        return not model.get_value(it, column).startswith(cp_text)

class Cb:
    def __init__(self):
        self.mainwindow = None
        
def edit(fname, mainwin=False):
    quit_cb = lambda w: gtk.main_quit()
    cb = Cb()
    w = gtk.Window()
    w.connect('delete-event', gtk.main_quit)
    cb.mainwindow = w
    e = EditWindow(cb, quit_cb=quit_cb)
    if fname != "":
        w.file_new()
    w.set_title("Culebra")
    w.add(e)
    w.maximize()
    w.show_all()
    w.set_size_request(0,0)

    w.dirname = os.getcwd()

    if mainwin: gtk.main()
    return

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        fname = sys.argv[-1]
    else:
        fname = ""
    edit(fname, mainwin=True)

