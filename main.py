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

# This module ties everything together. It handles the main loop and
# communication between components.

# profiling
from profiling import *
m = ProfMonitor('main.import')

from select import select

import phonetizer, mbrola_prog, sndoutput, version, config

import tracing
def trace(msg):
    mod = 'main'
    tracing.trace(mod+': '+msg)

~m

class SpeechServ:
    def __init__(self, appFeedClass):
        self.appfeed = appFeedClass()
        self.phozer = None
        self.mbrola = mbrola_prog.Mbrola()
        self.samplingRate = self.mbrola.voiceRate()
        self.expand = config.mbrola_t
        self.sndoutput = sndoutput.SndOutput(self.samplingRate)
    def roll(self):
        wait = self.sndoutput.inputSleepTime()
        if wait:
            trace('select ignoring mbrola')
            fds = [self.appfeed.selectfd()]
            if self.phozer:
                wait = min(wait, 0.15)
            m = ProfMonitor('main.delibWait')
            r,w,x = select(fds, [], fds, wait)
            ~m
        else:
            trace('selecting')
            fds = [self.appfeed.selectfd(), self.mbrola.selectfd()]
            if self.phozer:
                t = 0.15
            else:
                t = None
            r,w,x = select(fds, [], fds, t)
        fds_desc = {
            self.appfeed.selectfd(): 'appfeed',
            self.mbrola.selectfd(): 'mbrola'}
        trace('selected: [%s]'
              % ','.join([fds_desc[f] for f in r+x]))
        while self.appfeed.selectfd() in r+x:
            action,input = self.appfeed.handle()
            if action is 'M':
                trace('resetting')
                self.phozer = None
                self.mbrola.reset()
                self.sndoutput.reset()
            elif action is 'S':
                trace('new utterance: <%s>' % input)
                if not self.phozer:
                    trace('new phozer')
                    self.phozer = phonetizer.Phonetizer(self.samplingRate)
                self.phozer.feed(input)
                wait = 0
            elif action is 'T':
                self.expand = input
            if not self.appfeed.gotMore():
                break
        if self.phozer:
            spokenSamples = self.sndoutput.spokenPos()
            inx, finished = self.phozer.index(spokenSamples)
            if inx is not None:
                trace('send index %d' % inx)
                self.appfeed.sendIndex(inx)
            if finished:
                trace('phozer says finished')
                self.phozer = None
                self.sndoutput.reset()
                trace(profReport())
        if self.mbrola.selectfd() in r+x:
            trace('Getting from mbrola')
            sound, nsamples = self.mbrola.get()
            if sound and self.phozer:
                trace('passing mbrola output')
                self.sndoutput.give(sound)
                if nsamples:
                    trace('mbrola finished')
                    self.phozer.produced(nsamples)
                    if self.phozer.isDone():
                        trace('phozer tells sndoutput that it\'s got '
                              'everything')
                        self.sndoutput.allGiven()
        if not wait and self.phozer and self.mbrola.isFinished():
            trace('Getting phos')
            phos, dur = self.phozer.get(self.expand)
            if phos:
                trace('passing phonemes to mbrola')
                self.mbrola.say(phos, dur,self.expand)
    def run(self):
        self.phozer = phonetizer.Phonetizer(self.samplingRate)
        # FIXME: this introduces bogus indexes. They're filtered at
        # the appFeed level but that's not so clean.
        self.phozer.feed(version.banner)
        while 1:
            self.roll()
