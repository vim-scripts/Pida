# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: iconmaker.py 477 2005-07-29 21:22:08Z aafshar $
import gtk
import os
import shelve
import shutil

I = gtk.IconTheme()
I.set_custom_theme('Rodent')

f = open('iconmaker.data', 'r')
try:
    shutil.rmtree('iconbuild')
except:
    pass
try:
    os.remove('icons.dat')
except:
    pass
os.mkdir('iconbuild')
outfile = shelve.open('icons.dat')
for line in f:
    name, key = [s.strip() for s in line.split(' ')]
    i = I.load_icon(name, 15, 0)
    d = i.get_pixels()
    cs = i.get_colorspace()
    ha = i.get_has_alpha()
    bp = i.get_bits_per_sample()
    w = i.get_width()
    h = i.get_height()
    rs = i.get_rowstride()
    outfile[key] = d, (ha, bp, w, h, rs)
outfile.close()
w = gtk.Window()
w.connect('destroy', gtk.main_quit)
b = gtk.HBox()
w.add(b)
outfile = shelve.open('icons.dat')
cs = gtk.gdk.COLORSPACE_RGB
for i in outfile:
    d, a = outfile[i]
    pb = gtk.gdk.pixbuf_new_from_data(d, cs, *a)
    im = gtk.Image()
    im.set_from_pixbuf(pb)
    b.pack_start(im)
outfile.close()
w.show_all()
gtk.main()
