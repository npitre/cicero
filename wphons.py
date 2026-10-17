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

# Takes text as input and translates it to a list of phonemes.
# Shows applied rules as it goes.

import sys

import setencoding
import ttp

import tracing

def trace(msg):
    mod = 'wphons'
    tracing.trace(mod+': '+msg)

if __name__ == "__main__":
    setencoding.stdfilesEncoding()
    setencoding.decodeArgs()
    if len(sys.argv) > 1:
        words = sys.argv[1:]
    else:
        words = sys.stdin.readlines()
    words = [w.strip() for w in words]
    trace('Got %d words' % len(words))
    for i,w in enumerate(words):
        phons = ttp.word2phons(w,1)
        sys.stdout.write('%s -> %s\n' % (w,phons))
    sys.stdout.flush()
