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

# This module wraps up the details of managing a pipe to the MBROLA executable.

import os, fcntl, signal, popen2, struct, time
from select import select
from profiling import *

import tracing
def trace(msg):
    mod = 'mbrola_prog'
    tracing.trace(mod+': '+msg)

import config

class MbrolaError(Exception):
    pass

class Mbrola:
    def __init__(self):
        if not os.access(config.mbrola_prog_path, os.X_OK):
            raise MbrolaError('mbrola program path <%s> not executable'
                              % config.mbrola_prog_path)
        if not os.access(config.mbrola_voice, os.R_OK):
            raise MbrolaError('mbrola voice path <%s> not readable'
                              % config.mbrola_voice)
        cmd = '%s -e -f %g %s - -.wav' \
              % (config.mbrola_prog_path, config.mbrola_f, config.mbrola_voice)
        trace('mbrola cmd is <%s>' % cmd)
        self.p = popen2.Popen3(cmd, 1, 0)
        fcntl.fcntl(self.p.fromchild, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.p.childerr, fcntl.F_SETFL, os.O_NONBLOCK)
        self.p.tochild.write('#\n')
        self.p.tochild.flush()
        select([self.p.fromchild], [], [self.p.fromchild], 2.0)
        header = self.p.fromchild.read(44)
        self.checkForErrors()
        self.checkForErrors() # twice
        try:
            tag, self.rate = struct.unpack("8x8s8xi16x", header)
            trace('tag: %s' % tag)
            if tag != "WAVEfmt " :
                raise struct.error
        except struct.error:
            raise MbrolaError('Got something else than WAVE header '
                              +'from MBROLA')
        trace('Voice rate is %d' % self.rate)
        self.finished = 1
        self.estimatedSamples = self.finishFudge = self.producedSamples = 0
        self.lastErr = ''
        self.lastErrTime = 0
    def voiceRate(self):
        """Returns MBROLA voice's sampling rate"""
        return self.rate
    def say(self, str, dur, expand=config.mbrola_t):
        self.profMonTotal = ProfMonitor('mbrola_prog.total')
        self.profMonInitOut = ProfMonitor('mbrola_prog.initialOutput')
        #trace('Send to mbrola: <\n%s\n>' % str)
        self.p.tochild.write(';;T=%g\n' % expand)
        self.p.tochild.write(str)
        self.p.tochild.flush()
        self.finished = 0
        self.producedSamples = 0
        self.estimatedSamples = dur *self.rate /1000
        self.finishFudge = (192 +.00015*self.estimatedSamples) /expand
        trace('estimatedSamples %d, finishFudge %d'
              % (self.estimatedSamples, self.finishFudge))
    def isFinished(self):
        return self.finished
    def reset(self):
        trace('resetting mbrola')
        if not self.finished:
            trace('kill USR1 mbrola')
            os.kill(self.p.pid, signal.SIGUSR1)
            self.p.tochild.write('#\n')
            self.p.tochild.flush()
        self.get()
        self.finished = 1
        self.estimatedSamples = self.producedSamples = 0
    def checkForErrors(self):
        try:
            s = self.p.childerr.read()
        except IOError, x:
            if x.errno == 11:
                return
            raise
        if s:
            s = s.strip()
            self.lastErr = s
            self.lastErrTime = time.time()
            trace('MBROLA stderr: <%s>' % s)
        else:
            # EOF on stderr, assume mbrola died.
            pid, sts = os.waitpid(self.p.pid, os.WNOHANG)
            if pid == 0:
                s = 'mbrola closed stderr and did not exit'
            else:
                if os.WIFSIGNALED(sts):
                    sig = os.WTERMSIG(sts)
                    for k,v in signal.__dict__.iteritems():
                        if k.startswith('SIG') and v == sig:
                            signame = k
                            break
                        else:
                            signame = '%d' % sig
                    s = 'mbrola died by uncaught signal %s' %signame
                elif os.WIFEXITED(sts):
                    s = 'mbrola exited with status %d' %os.WEXITSTATUS(sts)
                else:
                    s = 'mbrola died and wait status is weird'
                if os.WCOREDUMP(sts):
                    s += ', dumped core'
                trace(s)
            if self.lastErr and time.time() -self.lastErrTime <1.0:
                s += ', with error "%s"' % self.lastErr
            raise MbrolaError(s)
    def selectfd(self):
        return self.p.fromchild
    def get(self):
        self.checkForErrors()
        try:
            sound = self.p.fromchild.read()
        except IOError, x:
            if x.errno == 11:
                return '', 0
            raise
        if self.finished:
            trace('Dropping %d extra MBROLA samples beyond estimated size'
                  % (len(sound)/2))
            return '', 0
        if self.profMonInitOut:
            ~self.profMonInitOut
            self.profMonInitOut = None
        self.producedSamples += len(sound)/2
        trace('Produced %d more samples, now %d'
              % (len(sound)/2, self.producedSamples))
        if self.producedSamples > self.estimatedSamples -self.finishFudge:
            trace('Assume finished')
            self.finished = 1
            nsamples = self.producedSamples
            ~self.profMonTotal
        else:
            nsamples = 0
        return sound, nsamples
