# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: debugger.py 352 2005-07-14 00:16:02Z gcbirzan $
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

# Copied from the bdb, pdb, Idle and eric3 debuggers

import gtk
import os
import cPickle as pickle
import types
import sys
import linecache
import pdb
import traceback
import pida.gobjectreactor as gobjectreactor
import cStringIO

class Debugger(object):
    def __init__(self, parentsock, childsock):
        self.reactor = gobjectreactor.Reactor(self, childsock, parentsock)
        self.reactor.start()
    
    def loop(self):
        while gtk.gdk.events_pending():
            gtk.main_iteration()
        

    def evaled(self, line, s):
        self.reactor.remote('eval', '%s\n%s' % (line, s))
        self.loop()

    def received(self, stack, tb):
        s = self.format_stack(stack)
        self.reactor.remote('stack', s)
        self.loop()
        #self.ipc.write('frame', [self.pdb.curindex], 32)

    def started(self):
        self.reactor.remote('started', '1')
        self.loop()
    
    def format_stack(self, stack):
        return pickle.dumps([self.format_stack_entry(f) for f in stack])

    def format_stack_entry(self, frame_lineno, lprefix=': '):
        import linecache, repr
        frame, lineno = frame_lineno
        filename = self.pdb.canonic(frame.f_code.co_filename)
        L = [filename, lineno]
        if frame.f_code.co_name:
             L.append(frame.f_code.co_name)
        else:
            L.append("<lambda>")
        if '__args__' in frame.f_locals:
            L.append(repr.repr(frame.f_locals['__args__']))
        else:
            L.append([])
        if '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            L.append(repr.repr(rv))
        else:
            L.append(None)
        line = linecache.getline(filename, lineno)
        if line:
            L.append(line.strip())
        else:
            L.append('')
        L.append(self.format_namespace(frame.f_locals))
        L.append(self.format_namespace(frame.f_globals))
        return L

    def format_namespace(self, nsdict):
        #return nsdict
        L = []
        ks = nsdict.keys()
        for k in ks:
            typ = type(nsdict[k])
            v = ''
            if typ in [int, str, long, float]:
                v = '%r' % (nsdict[k])
            else:
                v = typ.__name__
            L.append((k, v))
        #print L
        return L


class Pidadb(pdb.Pdb):

    def __init__(self, cb):
        self.cb = cb
        pdb.Pdb.__init__(self)
        self.prompt = 'dbg> '

    def interaction(self, frame, traceback):
        self.setup(frame, traceback)
        self.cb.received(self.stack, traceback)
        self.cmdloop()
        self.forget()

    def default(self, line):
        s = cStringIO.StringIO()
        oldstdout = sys.stdout
        sys.stdout = s
        pdb.Pdb.default(self, line)
        sys.stdout = oldstdout
        s.seek(0)
        self.cb.evaled(line.strip(), s.read())


def main():
    mainpyfile =  sys.argv[1]     # Get script filename
    parentsock = sys.argv[2]
    childsock = sys.argv[3]
    # Replace pdb's dir with script's dir in front of module search path.
    sys.path[0] = os.path.dirname(mainpyfile)
    client = Debugger(parentsock, childsock)
    pdb = Pidadb(client)
    client.pdb = pdb
    client.started()
    while 1:
        try:
            pdb._runscript(mainpyfile)
            if pdb._user_requested_quit:
                break
        except SystemExit:
            pass
            # In most cases SystemExit does not warrant a post-mortem session.
        except:
            traceback.print_exc()
            print "Uncaught exception. Entering post mortem debugging"
            print "Running 'cont' or 'step' will restart the program"
            t = sys.exc_info()[2]
            while t.tb_next is not None:
                t = t.tb_next
            pdb.interaction(t.tb_frame,t)
            print "Post mortem debugger finished. The "+mainpyfile+" will be restarted"


# When invoked as main program, invoke the debugger on a script
if __name__=='__main__':
    main()
