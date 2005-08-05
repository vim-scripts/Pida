# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: generate-api.py 352 2005-07-14 00:16:02Z gcbirzan $

###
# Copyright (c) 2005, Ali Afshar
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import sys

VERBOSE = True

IGNORED = ['__builtins__', '__file__']

def log(message):
    if VERBOSE:
        print message

def main(module_list):
    if not module_list:
        module_list.append('pida.plugin')
        generate_api(module_list)
        
def generate_api(module_list):        
    for name in module_list:
        doc = ModuleDoc(name)
        f = open('/home/ali/pidaapi.rst', 'w')
        f.write(doc.render())
        f.close()

class ObjectDoc(object):

    def __init__(self, obj, name=None):
        self.obj = obj
        if not name:
            name = obj.__name__
        self.name = name
        self.variables = []
        self.functions = []
        self.classes = []
        self.parse(self.obj)

    def parse(self, root_object):
        for item in dir(root_object):
            if not item in IGNORED:
                obj = getattr(root_object, item)
                if type(obj) == type:
                    if not item.startswith('__'):
                        print item
                        self.add_class(obj)
                elif hasattr(obj, 'func_code'):
                    self.add_function(obj)
                else:
                    self.add_variable(item, obj)


    def add_variable(self, name, value):
        if not name.startswith('_'):
            render_dict = {'name':name,
                           'value':value,
                           'doc':''}
            self.variables.append(VARIABLE_TEMPLATE % render_dict)

    def add_class(self, classobj):
        name = '.'.join([self.name, classobj.__name__])
        self.classes.append(ClassDoc(classobj, name))

    def add_function(self, funcobj):
        render_dict = {'name':funcobj.__name__,
                       'return':'',
                       'notes':'',
                       'args':''}
        fields = self.parse_doc(funcobj)
        main = fields.pop(0)
        fields = dict(fields)
        render_dict['doc'] = main[1]
        render_dict['summary'] = main[0]
        code = funcobj.im_func.func_code
        render_dict['fargs'] = ', '.join(code.co_varnames)

        args = {}
        notes = ''
        for field in fields:
            if field.startswith('param '):
                name = field.split(' ')[-1]
                args.setdefault(name, {})['body'] = fields[field]
            elif field.startswith('type '):
                name = field.split(' ')[-1]
                args.setdefault(name, {})['type'] = fields[field]
            elif field.startswith('return'):
                args.setdefault('__return__', {})['body'] = fields[field]
            elif field.startswith('note'):
                notes = fields[field]
        if '__return__' in args:
            render_dict['return'] = args['__return__']
            del args['__return__']
        arglist = []
        for arg in args:
            arglines = {'name':arg, 'body':'', 'type':''}
            if 'body' in args[arg]:
                arglines['body'] = args[arg]['body']
            if 'type' in args[arg]:
                arglines['type'] = args[arg]['type']
            arglist.append(ARGUMENT_TEMPLATE % arglines)
        render_dict['args'] = '\n'.join(arglist)
        render_dict['notes'] = notes
        self.functions.append(FUNCTION_TEMPLATE % render_dict)

    def render(self, indent=0):
        render_dict = {}
        render_dict['name'] = self.name
        render_dict['variables'] = '\n'.join(self.variables)
        render_dict['functions'] = '\n'.join(self.functions)
        classes = []
        for c in self.classes:
            classes.append(c.render())
        classes = '\n'.join(classes)
        render_dict['classes'] = classes
        s = self.template() % render_dict
        return s

    def template(self):
        return WIKI_TEMPLATE
        
    def parse_doc(self, obj):
        render_dict = {}
        doc = obj.__doc__.strip()
        doclines = doc.split('@')
        main = doclines.pop(0).split('\n', 1)
        summary = main.pop(0)
        body = (len(main) and main.pop()) or ''
        fields = [[summary, self.format_paragraph(body)]]
        for line in doclines:
            try:
                field, value = line.split(':', 1)
                fields.append([field, self.format_paragraph(value)])
            except ValueError:
                log('Bad tag obj.__name__')
        return fields
        
    def format_paragraph(self, paragraph):
        lines = paragraph.strip().splitlines()
        return ' '.join([line.strip() for line in lines])
        
class ModuleDoc(ObjectDoc):
    """A document for a module."""

    def __init__(self, name):
        mod = __import__(name, {}, {}, [True])
        ObjectDoc.__init__(self, mod, name)

class ClassDoc(ObjectDoc):
    def template(self):
        return CLASSES_TEMPLATE
    

WIKI_TEMPLATE = """== Api for %(name)s ==
=== Variables ===
%(variables)s
%(classes)s
=== Functions ===
%(functions)s"""

CLASSES_TEMPLATE = """=== class %(name)s ===
==== Variables (%(name)s) ====
%(variables)s
==== Methods (%(name)s) ====
%(functions)s"""

VARIABLE_TEMPLATE = """%(name)s
%(value)s
%(doc)s"""

FUNCTION_TEMPLATE = """'''%(name)s'''

 %(name)s(%(fargs)s)
:'''%(summary)s'''
:%(doc)s
%(args)s
:%(return)s
:%(notes)s
----"""

CLASS_TEMPLATE = """'''Class %(name)s
%(body)s"""

ARGUMENT_TEMPLATE = """::; %(name)s : %(body)s
::: type - %(type)s"""

if __name__ == '__main__':
    main(sys.argv[1:])

