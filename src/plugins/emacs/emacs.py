# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: emacs.py 352 2005-07-14 00:16:02Z gcbirzan $
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

#

import gtk
import gobject
import socket
import os
#
#    s.send('''(gnuserv-edit-files '(x ":0.0") '((1 . "/home/ali/goo.py")))\4''')
#(gnuserv-eval '(progn (EXPR)))
#gnuserv-edit-file




class EmacsClient(object):
    
    def __init__(self, cb):
        self.cb = cb
        self.rbuf = ''
        self.bufferlist = None
        self.currentbuffer = None
        self.lastfirst = None
        self.callbacks = {}
        self.connected = False
        gobject.timeout_add(1000, self.poll_emacs)
        self.pid = None
    def received(self, data, sock):
        sockno = sock.fileno()
        if sockno in self.callbacks:
            self.callbacks[sockno](data)
            del self.callbacks[sockno]
        
    def launch(self):
        if self.pid:
            if os.waitpid(self.pid, os.WNOHANG)[0]:
                self.pid = None
        else:
            pid = os.fork()
            if pid == 0:
                command = self.cb.registry.commands.xemacs.value()
                args = ['pida-emacs', '-f', 'gnuserv-start']
                os.execvp(command, args)
            else:
                self.pid = pid

    def send(self, message, callback=None):
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self._socket.connect('/tmp/gsrvdir1000/gsrv')
            self._socket.send('\4%s\4' % message)
            if callback:
                self.callbacks[self._socket.fileno()] = callback
                gobject.io_add_watch(self._socket, gobject.IO_IN, self.cb_readable)
        except socket.error, e:
            ecode = e.args[0]
            if ecode == 111:
                #self.launch()
                self.cb.evt('disconnected')
            #print ecode

    def func(self, expression, callback):
        s = "(gnuserv-eval '(progn (%s)))" % expression
        self.send(s, callback)
        
    def edit_file(self, filename):
        s = '''(gnuserv-edit-files '(x ":0.0") '((1 . "%s")) 'quick)''' % filename
        self.send(s, None)

    def cb_readable(self, sock, condition):
        data = sock.recv(1024)
        self.rbuf = '%s%s' % (self.rbuf, data)
        lines = self.rbuf.split('\n')
        if len(lines) > 1:
            self.received(lines.pop(0), sock)
            self.rbuf = lines.pop(0)
            return False
        else:
            return True
                     
    def poll_emacs(self):
        self.get_bufferlist()
        #self.get_currentbuffer()
        return True

    def get_bufferlist(self):
        def reply(bl):
            newlist =  [[i] + [n.strip() for n in b.split('\5')] for i, b in \
                  enumerate(bl.split('\6'))]
            #if newlist != self.bufferlist:
            if not self.bufferlist or self.check_newlist(newlist):
                self.bufferlist = newlist
                self.feed_bufferlist()

        s = ('''mapconcat '''
                '''(lambda (b) '''
                    '''(concat (buffer-name b) "\5" (buffer-file-name b)))'''
                '''(buffer-list) '''
                '''"\6"''')
        self.func(s, reply)

    def check_newlist(self, newlist):
        old = [[i[2], None] for i in self.bufferlist]
        new = [[i[2], None] for i in newlist]
        
        if self.lastfirst != new[0]:
            self.get_currentbuffer()
        self.lastfirst = new[0]
        if len(old) == len(new):
            return dict(old) != dict(new)
        else:
            return True
        
        

    def get_currentbuffer(self):
        def reply(bn):
            bn = bn.strip()
            for num, name, fn in self.bufferlist:
                if name == bn:
                    self.cb.evt('bufferchange', num, fn)
                    break
        self.func('window-buffer', reply)

    def change_buffer(self, buffernumber):
        for num, name, fn in self.bufferlist:
            if num == buffernumber:
                self.func('switch-to-buffer "%s"' % name, None)
                break
    def feed_bufferlist(self):
        sendlist = [[l[0], l[2]] for l in self.bufferlist if l[2]]
        self.cb.evt('bufferlist', sendlist)

    def gotoline(self, line):
        self.func('goto-line %s' % line, None)

    def close_buffer(self):
        self.func('kill-buffer nil', None)

