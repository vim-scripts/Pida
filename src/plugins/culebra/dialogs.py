# -*- coding: utf-8 -*-
#Copyright Fernando San Martín Woerner <fsmw@gnome.org>
# $Id: dialogs.py 440 2005-07-22 16:24:53Z snmartin $
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
#
# This file is part of Culebra project.
#

import gtk

import os

def InputBox(title, label, parent, text=''):
    dlg = gtk.Dialog(title, parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_OK, gtk.RESPONSE_OK,
                      gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    lbl = gtk.Label(label)
    lbl.show()
    dlg.vbox.pack_start(lbl)
    entry = gtk.Entry()
    if text: entry.set_text(text)
    entry.show()
    dlg.vbox.pack_start(entry, False)
    resp = dlg.run()
    text = entry.get_text()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return text

def OpenFile(title, parent=None, dirname=None, fname=None, mask = None):

    dlg = gtk.FileChooserDialog(title, parent,
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                         gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_CANCEL))

    if fname:
        dlg.set_current_folder(os.path.dirname(fname))
    elif dirname:
        dlg.set_current_folder(dirname)
    else:
        dlg.set_current_folder(os.getcwd())

    filter = gtk.FileFilter()
    filter.add_mime_type("text/x-python")

    if not mask is None:
        filter.add_pattern(mask)

    dlg.set_filter(filter)
    dlg.set_local_only(True)
    resp = dlg.run()
    fname = dlg.get_filename()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return fname

def SaveFile(title, parent=None, dirname=None, fname=None):
    dlg = gtk.FileChooserDialog(title, parent,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                                         gtk.STOCK_CANCEL,
                                         gtk.RESPONSE_CANCEL))
    if fname:
        dlg.set_filename(fname)
    elif dirname:
        dlg.set_current_folder(dirname)
    dlg.set_local_only(True)
    resp = dlg.run()
    fname = dlg.get_filename()
    dlg.hide()
    if resp == gtk.RESPONSE_CANCEL:
        return None
    return fname

