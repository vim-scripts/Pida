#!/bin/sh
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
# $Id: setup.py 485 2005-08-02 19:04:35Z aafshar $
#Copyright (c) 2005 Alejandro Mery <amery@geeks.cl> 

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

#Run or symlink this script

PIDA=$( readlink -f $0 )
PIDADIR=${PIDA%/extras/pida-local.sh}
PIDA=${PIDADIR}/scripts/pida

if [ ! -e ${PIDADIR}/.lib/pida ]; then
	mkdir -p ${PIDADIR}/.lib
	ln -s ${PIDADIR}/src ${PIDADIR}/.lib/pida
fi
PYTHONPATH="${PIDADIR}/.lib/:$PYTHONPATH" exec python $PIDA
