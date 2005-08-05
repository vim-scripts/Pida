# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: registry.py 388 2005-07-20 23:38:18Z aafshar $
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


import os
import config
import ConfigParser as configparser

class BadRegistryKey(Exception):
    pass

class BadRegistryGroup(Exception):
    pass

class BadRegistryValue(Exception):
    pass

class BadRegistryData(Exception):
    pass

class BadRegistryDefault(Exception):
    pass


class RegistryItem(object):
    DISPLAY_WIDGET = config.ConfigEntry

    def __init__(self, name, default, doc):
        self._name = name
        self.doc = doc
        self._value = None
        self._default = default

    def setdefault(self):
        self.set(self._default)

    def validate(self, value):
        return True

    def unserialize(self, data):
        return data

    def serialize(self):
        return '%s' % self.value

    def load(self, data):
        try:
            value = self.unserialize(data)
        except Exception, e:
            # Any unserialisation error is a failure
            return False
        try:
            self.set(value)
            return True
        except BadRegistryEntry:
            return False

    def set(self, value):
        if self.validate(value):
            self._value = value
        else:
            raise BadRegistryValue, value

    def value(self):
        return self._value

    def __repr__(self):
        return ('Registry Value typ=%s name=%s value=%s default=%s '
                'doc=%s' % (self.__class__.__name__, self._name,
                           self._value, self._default, self.doc))
                    

class RegistryGroup(object):
    
    def __init__(self, name, doc):
        self._name = name
        self._doc = doc

    def add(self, name, typ, default, doc):
        try:
            entry = typ(name, default, doc)
            setattr(self, name, entry)
            return entry
        except BadRegistryDefault:
            return False

    def delete(self, name):
        delattr(self, name)

    def __iter__(self):
        for child in dir(self):
            obj = getattr(self, child)
            if isinstance(obj, RegistryItem):
                yield obj
        
    def get(self, childname):
        if hasattr(self, childname):
            return getattr(self, childname)
        else:
            raise BadRegistryKey, '"%s"' % childname

    def _get_doc(self):
        return self._doc

    doc = property(_get_doc)

class Directory(RegistryItem):
    DISPLAY_WIDGET = config.ConfigFolder
    def validate(self, value):
        return os.path.isdir(value)
        
class CreatingDirectory(Directory):
    def validate(self, value):
        if Directory.validate(self, value):
            return True
        else:
            os.makedirs(value)
            return Directory.validate(self, value)

class File(RegistryItem):
    DISPLAY_WIDGET = config.ConfigFile
    pass

class MustExistFile(File):

    def validate(self, value):
        return os.path.exists(value)

class WhichFile(File):
    
    def setdefault(self):
        path = which(self._default)
        if path:
            self.set(path)
        else:
            self.set('')

class Font(RegistryItem):
    DISPLAY_WIDGET = config.ConfigFont

class Boolean(RegistryItem):
    DISPLAY_WIDGET = config.ConfigBoolean
    def unserialize(self, data):
        try:
            val = int(data)
        except ValueError:
            val = int(data[0].lower() in ['t'])
        except:
            raise BadRegistryData
        return val

class Integer(RegistryItem):
    DISPLAY_WIDGET = config.ConfigInteger
    def unserialize(self, data):
        try:
            val = int(data)
        except:
            raise BadRegistryData
        return val

class List(RegistryItem):
    DISPLAY_WIDGET = config.ConfigList

class Color(RegistryItem):
    DISPLAY_WIDGET = config.ConfigColor

class Registry(object):

    def __init__(self, filename):
        self.filename = filename
        self.optparseopts = {}

    def add_group(self, name, doc):
        group = RegistryGroup(name, doc)
        setattr(self, name, group)
        return group

    def iter_groups(self):
        for name in dir(self):
            obj = getattr(self, name)
            if isinstance(obj, RegistryGroup):
                yield obj

    def iter_items(self):
        for group in self.iter_groups():
            for option in group:
                yield group, option
        
    def iter_pretty(self):
        for g, i in self.iter_items():
            yield '%s.%s = %s' % (g._name, i._name, i.value())

    def load_file(self):
        tempopts = configparser.ConfigParser()
        if os.path.exists(self.filename):
            f = open(self.filename, 'r')
            tempopts.readfp(f)
        for group, option in self.iter_items():
            if tempopts.has_option(group._name, option._name):
                data = tempopts.get(group._name, option._name)
                if not option.load(data):
                    option.setdefault()
            else:
                option.setdefault()

    def load_opts(self):
        for k in self.optparseopts:
            groupname, childname = k
            data = self.optparseopts[k]
            group = getattr(self, groupname)
            option = getattr(group, childname)
            option.load(data)

    def load(self):
        self.load_file()
        self.load_opts()

    def save(self):
        f = open(self.filename, 'w')
        f.write(CONFIG_FILE_INTRO)
        for group in self.iter_groups():
            f.write('\n[%s]\n' % group._name)
            for option in group:
                f.write('# %s\n' % option._name)
                f.write('# %s\n' % option.doc)
                f.write('# default value = %s\n' % option._default)
                f.write('%s = %s\n\n' % (option._name, option.value()))
        f.close()

    def prime_optparser(self, optparser):
        if hasattr(optparser, 'add_option'):
            def setfilename(opt, opt_str, value, parser):
                self.filename = value
            def setitem(opt, opt_str, value, parser):
                if value.count('='):
                    name, value = value.split('=', 1)
                    if name.count('.'):
                        group, child = name.split('.', 1)
                        self.optparseopts[(group, child)] = value
            optparser.add_option('-f', '--registry-file', type='string', nargs=1,
                                 action='callback', callback=setfilename)
            optparser.add_option('-c', '--config', type='string', nargs=1,
                                 action='callback', callback=setitem)
            
def which(name):
    ''' Returns the path of the application named name using 'which'. '''
    p = os.popen('which %s' % name)
    w = p.read().strip()
    p.close()
    if len(w):
        if 'command not found' in w:
            return None
        else:
            return w
    else:
        return None

CONFIG_FILE_INTRO = ('#This is an automatically generated Pida config file.\n'
             '#Please edit it, your changes will be preserved (if valid).\n'
             '#If you want a fresh config file, delete it.\n\n'
             '#Notes:\n'
             '#Boolean values are 1 or 0\n'
             '#Blank lines are ignored as are lines beginning #\n'
             '#(comments).\n\n')

if __name__ == '__main__':

    r = Registry('/home/ali/tmp/reg')
    g = r.add_group('first', 'The docs for first group')
    e = g.add('blahA', Boolean, 0, 'docs for blahA')
    e = g.add('blahB', Boolean, 1, 'docs for blahB')
    import optparse
    op = optparse.OptionParser()
    r.prime_optparse(op)
    import sys
    sys.argv.append('--config.first.blahB=1')
    #sys.argv.append('-C/home/ali/tmp/reg2')
    print op.parse_args()
    r.load()
    #r.save()
    #e.load('True')
    #print r.groups
    print r.first.blahA
    #r.save()


