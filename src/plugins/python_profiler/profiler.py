# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: profiler.py 352 2005-07-14 00:16:02Z gcbirzan $
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


import profile
import os
import sys
import pida.gtkextra as gtkextra
import pida.gobjectreactor as gobjectreactor
import tempfile
import pickle
import gtk


class Profiler(object):
    def __init__(self, parentsocket, childsocket):
        #self.ipc = gtkextra.IPWindow(self)
        #self.ipc.reset(long(sid))
        #self.ipc.connect()
        self.reactor = gobjectreactor.Reactor(self, childsocket, parentsocket)
        self.reactor.start()

    def profile(self, filename):
        p = profile.Profile()
        com = 'execfile("%s")' % filename
        p.run(com)
        p.snapshot_stats()
        outf = tempfile.mktemp('pida-profile')
        f = open(outf, 'w')
        s = pickle.dump(p.stats, f)
        f.close()
        #self.ipc.write('stats', outf, 8)
        self.reactor.remote('stats', outf)
        while gtk.events_pending():
            gtk.main_iteration()


def main(filename, parentsocket, childsocket):
    profiler = Profiler(parentsocket, childsocket)
    profiler.profile(filename)

if __name__ == '__main__':
    print sys.argv
    main(sys.argv[1], sys.argv[2], sys.argv[3])
