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

# This is some glue between main and ttp.
# This module splits the input into smaller chunks (so we don't process
# everything in one go and can start to speak earlier).
# It also manages tracking speech position with indexes.

import re
# profiling

import ttp
import config
from profiling import *

import tracing
def trace(msg):
    mod = 'phonetizer'
    tracing.trace(mod+': '+msg)

munch_rgxp = re.compile(
    ur'((?:\s*\S){50}.*?'
    ur'[^\.!\?\s]{3,}[\.!\?]*[\]\)\}"]*[\.!\?]+\s+)'
    ur'(\W*[A-ZÇÉÀÈÙÂÊÎÔÛ].*$)',
    re.S)
bigsplit_rgxp = re.compile(
    r'((?:(?:\s*\S){50}.*?' '\n\n' '+)'
       r'|(?:.{450}.*?\s+))'
    r'(.*$)',
    re.S)

class Phonetizer:
    def __init__(self, rate):
        self.rate = rate
        self.input = ''
        self.inputLen = 0
        self.mbrolaSamples = 0
        self.gotMbrolaTotal = 0
        self.lastInx = 0
        self.indexes = [(0,0)]
        self.consumedBytes = 0
        self.totalDur = 0
        self.getInput = ProfProxy('phonetizer.splitting', self.getInput)
    def feed(self, input):
        self.input += input
        self.inputLen += len(input)
    def getInput(self):
        if not self.input:
            trace('No more input')
            return None
        m = munch_rgxp.match(self.input)
        if m:
            txt = m.group(1)
            self.input = m.group(2)
        else:
            txt = self.input
            self.input = ''
        if len(txt) > 600:
            m = bigsplit_rgxp.match(txt)
            if m:
                txt = m.group(1)
                self.input = m.group(2) + self.input
        return txt
    def get(self, expand=config.mbrola_t):
        txt = self.getInput()
        if txt is None:
            assert self.inputLen == self.consumedBytes
            assert self.inputLen == self.indexes[-1][1]
            return None, 0
        trace('Input chunk len %d' % len(txt))
        out, indexes = ttp.process(txt)
        trace('%d phonemes, %d indexes'
              % (len(out.split('\n')), len(indexes)))
        dur = indexes[-1][0] *expand
        indexes = [((self.totalDur +t*expand)*self.rate/1000,
                    b+self.consumedBytes) \
                   for t,b in indexes]
        self.indexes.extend(indexes)
        trace('duration %dms, consumed input bytes %d' % (dur, len(txt)))
        self.totalDur += dur
        self.consumedBytes += len(txt)
        if dur == 0:
            trace('0 duration phonemes')
            return None, 0
        return out, dur
    def isDone(self):
        return not self.input
    def produced(self, nsamples):
        """Main calls back in here with actual output length from mbrola,
        before calling get() again."""
        self.mbrolaSamples += nsamples
        if not self.input:
            self.gotMbrolaTotal = 1
            trace('phonemes duration %dms, mbrola output %dsamples'
                  % (self.totalDur, self.mbrolaSamples))
            while self.indexes and self.indexes[-1][0] >= self.mbrolaSamples:
                self.indexes.pop(-1)
            self.indexes.append( (self.mbrolaSamples, self.consumedBytes) )
    def index(self, spokenSamples):
        while len(self.indexes) >1 and self.indexes[1][0] <= spokenSamples:
            i = self.indexes.pop(0)
            trace('pop index %d %d' % i)
        inx = self.indexes[0][1]
        trace('index for %d samps -> %d bytes'
              % (spokenSamples, inx))
        if inx > self.lastInx:
            self.lastInx = inx
        else:
            inx = None
        finished = not self.input and len(self.indexes) == 1
        return inx, finished
