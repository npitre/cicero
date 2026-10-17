#!/usr/bin/python
# -*- coding: utf-8
# This file is part of Cicero TTS.
#   Cicero TTS: A Small, Fast and Free Text-To-Speech Engine.
#   Copyright (C) 2003-2008 Nicolas Pitre  <nico@fluxnic.net>
#   Copyright (C) 2003-2008 Stéphane Doyon <steph@electron9.net>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2.
#   See the accompanying COPYING file for more details.
#
#   This program comes with ABSOLUTELY NO WARRANTY.

# Takes text as input and shows the output of the filters stage.

import sys

import setencoding
import ttp

def trace0(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()
def trace(msg):
    trace0(msg+'\n')
def noop_trace(msg):
    pass

if __name__ == "__main__":
    setencoding.decodeArgs()
    setencoding.stdfilesEncoding()
    if len(sys.argv) > 1:
        words = sys.argv[1:]
        trace = trace0 = noop_trace
    else:
        words = sys.stdin.readlines()
    words = [w.strip() for w in words]
    trace('Got %d words' % len(words))
    for i,w in enumerate(words):
        trace0('%6d/%6d   \r' % (i+1,len(words)))
        str = ttp.word2filtered(w)
        sys.stdout.write('"%s" -> "%s"\n' % (w,str))
    sys.stdout.flush()
    trace('done          ')
