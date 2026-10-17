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

# This module handles the simplistic protocol of the BRLTTY
# ExternalSpeech driver.
# We are executed in a pipe so this module takes over stdin and stdout
# for communication with BRLTTY.
# Two commands on input: shutup or speak request.
# In the other direction we send back indexes to track the current
# listening position.

import os, sys, struct

import setencoding
import tracing
def trace(msg):
    mod = 'appfeed'
    tracing.trace(mod+': '+msg)

class ProtoError(Exception):
    pass

class AppFeed:
    def __init__(self):
        # make stdout/stderr unbuffered
        sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', 0)
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)
        setencoding.stdfilesEncoding(None,None,0)
    def selectfd(self):
        return sys.stdin
    def sendIndex(self, inx):
        d = struct.pack('>H', inx)
        try:
            sys.stdout.write(d)
            sys.stdout.flush()
        except IOError, x:
            if x.errno == 32:
                trace('Exit on broken pipe')
                sys.exit(0)
            else:
                raise
    def handle(self):
        code = sys.stdin.read(1)
        if not code:
            trace('Exit on EOF')
            sys.exit(0)
        code = struct.unpack('B', code)[0]
        trace('code %d' % code)
        if code == 1:
            trace('Mute req')
            return 'M',None
        elif code == 2 or code == 4:
            trace('Speak req')
            d = sys.stdin.read(4)
            size, attribsize = struct.unpack('>HH', d)
            trace('size %d, attribsize %d' % (size, attribsize))
            txtbuf = sys.stdin.read(size)
            attrbuf = sys.stdin.read(attribsize)
            # Just discard that for now
            # BRLTTY sends text encoded with ISO-8859-1
            encoding = 'iso-8859-1'
            if code == 4:
                encoding = 'utf8'
            txtbuf = txtbuf.decode(encoding)
            trace('txt: <%s>' % txtbuf[:50])
            self.sendIndex(0)
            return 'S',txtbuf
        elif code == 3:
            trace('Time scale')
            d = sys.stdin.read(4)
            expand = struct.unpack('>f', d)[0]
            trace('timescale %g' % expand)
            return 'T',expand
        else:
            raise ProtoError('Unrecognized command code %d' % code)
    def gotMore(self):
        return 0
