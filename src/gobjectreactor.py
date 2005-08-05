# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: gobjectreactor.py 352 2005-07-14 00:16:02Z gcbirzan $
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


"""
A Symmetrical Unix Domain Socket UDP remote procedure protocol.
"""

# gobject import
import gobject

# system imports
import os
import socket

class Reactor(object):

    def __init__(self, reactor, localsocketfile, remotesocketfile):
        self.reactor = reactor
        self.socketfile = localsocketfile
        self.remote_socketfile = remotesocketfile
        self.read_buffer = ''
         
    def start(self):
        if os.path.exists(self.socketfile):
            os.remove(self.socketfile)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(self.socketfile)
        gobject.io_add_watch(self.socket, gobject.IO_IN, self.cb_read)
    
    def stop(self):
        gtk.main_quit()

    def cb_read(self, socket, condition):
        if condition == gobject.IO_IN:
            data, address = socket.recvfrom(6024)
            self.received_data(data)
        return True

    def send(self, data):
        self.socket.sendto(data, self.remote_socketfile)

    def local(self, command, *args):
        commandname = 'do_%s' % command
        if hasattr(self.reactor, commandname):
            getattr(self.reactor, commandname)(*args)

    def remote(self, command, *args):
        commandstring = '%s\1%s\0' % (command, '\1'.join(args))
        self.send(commandstring)

    def received_data(self, data):
        self.read_buffer = '%s%s' % (self.read_buffer, data)
        self.process_data()

    def process_data(self):
        lines = self.read_buffer.split('\0')
        self.read_buf = lines.pop()
        for line in lines:
            self.received_line(line)

    def received_line(self, line):
        args = line.split('\1')
        command = args.pop(0)
        self.local(command, *args)

