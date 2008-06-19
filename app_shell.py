# -*- coding: utf-8
# This file is part of Cicero TTS.
#   Cicero TTS: A Small, Fast and Free Text-To-Speech Engine.
#   Copyright (C) 2003-2008 Nicolas Pitre  <nico@cam.org>
#   Copyright (C) 2003-2008 Stéphane Doyon <s.doyon@videotron.ca>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2.
#   See the accompanying COPYING file for more details.
#
#   This program comes with ABSOLUTELY NO WARRANTY.

# This module handles a simplisticshell-like interface to TTS.
# Text received on stdin is spoken out. Each word is written back 
# to stdout after it has been spoken.
# An empty line causes a shutup/mute command.
# EOF causes the tts program to exit.
# This interface is meant to be simple, not feature-full.

import os, sys, fcntl

import setencoding
import tracing

def trace(msg):
    mod = 'shell'
    tracing.trace(mod+': '+msg)

class AppFeed:
    def __init__(self):
        sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', 0)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)
        setencoding.stdfilesEncoding()
        self.pendingTxt = ''
        self.processedTxt = ''
        self.lastInx = 0
    def selectfd(self):
        return sys.stdin
    def sendIndex(self, inx):
        n = inx-self.lastInx
        if n>0 and self.processedTxt:
            self.lastInx = inx
            sys.stdout.write(self.processedTxt[:n])
            sys.stdout.flush()
            self.processedTxt = self.processedTxt[n:]
            if not self.processedTxt:
                self.lastInx = 0
                sys.stdout.write('\n')
    def handle(self):
        if self.pendingTxt:
            input = self.pendingTxt
            self.pendingTxt = ''
        else:
            try:
                input = sys.stdin.read()
            except IOError, x:
                if x.errno == 11:
                    return 'M',None
                raise
            if input == '':
                trace('Exiting on EOF')
                sys.exit(0)
            if input[0] == '\n':
                trace('Got empty line: muting')
                self.pendingTxt = input[1:]
                self.processedTxt = ''
                self.lastInx = 0
                sys.stdout.write('\n')
                return 'M',None
        self.processedTxt += input
        return 'S',input
    def gotMore(self):
        return not not self.pendingTxt
