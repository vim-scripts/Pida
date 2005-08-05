# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: setup.py 485 2005-08-02 19:04:35Z aafshar $
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


from distutils.core import setup

import os
import sys
import shutil

VERBOSE = True

def log(message):
    if VERBOSE:
        print 'Pida:', message

if sys.argv[-1] == 'upgrade':
    log('Preparing for upgrade')
    for path in sys.path:
        if path and os.path.exists(path):
            for dirname in os.listdir(path):
                dirpath = os.path.join(path, dirname)
                if os.path.isdir(dirpath) and dirpath.count(sys.prefix):
                    for packagename in os.listdir(dirpath):
                        if packagename == 'pida':
                            packagepath = os.path.join(dirpath, packagename)
                            log('Pida found at %s' % packagepath)
                            ri = raw_input('Delete old Pida '
                                           '(reccommended) Y/N? ')
                            if ri[0].lower() == 'y':
                                log('Deleting %s' % packagepath)
                                try:
                                    shutil.rmtree(packagepath)
                                except OSError, e:
                                    log('Failed to remove old Pida: %s' % e)
                            else:
                                log('Not deleting.')
    sys.argv.pop()
    sys.argv.append('install')
                                                  

log('Preparing core')
packages = ['pida',
            'pida.configuration',
            'pida.plugins']

log('Preparing plugins')
plugindir = os.path.join('src', 'plugins')
for plugin in os.listdir(plugindir):
    if not plugin[0] in ['.', '_']:
        log('Adding plugin "%s"' % plugin)
        packages.append('pida.plugins.%s' % plugin)

log('Performing setup.')
setup(name='pida',
    version='0.2.2pre',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    url='http://pida.berlios.de',
    download_url='http://pida.berlios.de/index.php/PIDA:Downloads',
    description=('A Python IDE written in Python and GTK, '
                 'which uses Vim as its editor.'),
    long_description='Please visit the Pida website for more details.',
    packages=packages,
    package_dir = {'pida': 'src'},
    scripts=['scripts/pida'],
    data_files=[(os.path.join('share', 'pida'), ['data/icons.dat',
                                                 'data/pidalogo.png'])],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development']
      
      )
