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

# This module deals with output to soundcard through OSS using
# python's ossaudiodev module.
# It starts off a new thread to feed audio in a timely manner. It
# handles buffering and provides the current listening position.

import ossaudiodev
from threading import *
import struct, sys, time, array, fcntl

import tracing
def trace(msg):
    mod = 'sndoutput'
    tracing.trace(mod+': '+msg)

import config

CHUNK = 2048 # samples

# Buffer max between 3 and 5secs of audio
WAIT_HI_THRESH = 6.0
WAIT_LOW_THRESH = 4.0

def mkInt(x):
    return struct.unpack('i', struct.pack('I', x))[0]

SNDCTL_DSP_SETFRAGMENT = mkInt(0xc004500aL)
FRAG = mkInt((0xFFFFL << 16) | 11)
FRAGCODE = array.array('B', struct.pack('i', FRAG))

class SndOutput(Thread):
    def __init__(self, rate):
        Thread.__init__(self)
        self.rate = rate
        self.lock = Lock()
        self.condMoreInput = Condition(self.lock)
        self.buf = ''
        self.pendingBuf = ''
        self.finishFlag = self.pendingFinishFlag = 0
        self.resetFlag = 0
        self.spokenSamps = 0
        self.err = None
        self.setDaemon(1)
        self.dsp = None
        self.bufsize = -1
        self.silence = ''
        self._open()
        self.dsp.close()
        self.dsp = None
        self.start()
    def checkErr(self):
        """Check if thread died and report error."""
        if self.err:
            raise self.err[0], self.err[1], self.err[2]
    def reset(self):
        """Call this to reset spokenSamps and/or to interrupt."""
        self.checkErr()
        self.lock.acquire()
        self.resetFlag = 1
        self.buf = self.pendingBuf = ''
        self.finishFlag = self.pendingFinishFlag = 0
        self.spokenSamps = 0
        self.condMoreInput.notify()
        self.lock.release()
    def inputSleepTime(self):
        """Returns how long we recommend the app to go to sleep, nonzero when
        we have too much audio data buffered."""
        self.checkErr()
        self.lock.acquire()
        if float(len(self.buf)/2) /self.rate > WAIT_HI_THRESH:
            t = float(len(self.buf)/2) /self.rate - WAIT_LOW_THRESH
        else:
            t = 0
        self.lock.release()
        return t
    def give(self, buf):
        """Provide new sound data to be played."""
        self.checkErr()
        self.lock.acquire()
        if self.finishFlag:
            self.pendingBuf += buf
            self.pendingFinishFlag = 0
            trace('give %d into pending buf' % len(buf))
        else:
            self.buf += buf
            trace('give %d into main buf' % len(buf))
        self.condMoreInput.notify()
        self.lock.release()
    def allGiven(self):
        """Inform that no more sound might be coming. This MUST be called at
        the end of an utterance, but more input can still be appended
        afterward if necessary."""
        self.checkErr()
        self.lock.acquire()
        if self.pendingBuf:
            self.pendingFinishFlag = 1
            trace('set pendingFinishFlag')
        else:
            self.finishFlag = 1
            trace('set finishFlag')
        self.condMoreInput.notify()
        self.lock.release()
    def spokenPos(self):
        """Returns number of samples played out for this utterance."""
        self.checkErr()
        self.lock.acquire()
        s = self.spokenSamps
        self.lock.release()
        return s
    def _open(self):
        if not self.dsp:
            start = time.time()
            while 1:
                try:
                    self.dsp = ossaudiodev.open(config.snd_dev, 'w')
                    break
                except IOError, x:
                    if x.errno != 16:
                        raise
                    trace('device is busy')
                    if self.bufsize==-1 and time.time() -start > 4.0:
                        raise 'Sound device is busy'
                    time.sleep(0.5)
            self.dsp.setparameters(ossaudiodev.AFMT_S16_LE, 1, self.rate, 0)
            fcntl.ioctl(self.dsp.fileno(), SNDCTL_DSP_SETFRAGMENT, FRAGCODE, 1)
            self.bufsize = self.dsp.bufsize()
            self.silence = struct.pack('H', 0)*self.bufsize
    def _write(self, buf):
        assert len(buf)/2 >= CHUNK
        b = buf[:2*CHUNK]
        self.lock.release()
        try:
            r = self.dsp.write(b)
        except IOError, x:
            if x.errno != 11:
                raise
            r = 0
        self.lock.acquire()
        return r
    def run(self):
        try:
            self.run2()
        except:
            self.err = sys.exc_info()
            try:
                self.lock.release()
            except thread.error:
                pass
    def run2(self):
        self.writtenSamps = 0
        self.silentSamps = 0
        self.lock.acquire()
        while 1:
            while 1:
                # we will wait unless...
                if self.resetFlag:
                    break
                if self.finishFlag:
                    if self.buf or self.pendingBuf or self.dsp:
                        # utterance still in progress
                        break
                else:
                    enough = (self.dsp and CHUNK) or 3*CHUNK
                    if len(self.buf)/2 >= enough:
                        break
                    if self.dsp:
                        trace('Not enough in buf: only %d' % (len(self.buf)/2))
                # So either utterance finished,
                # or not enough input to start and we know more is coming,
                # or not enough input for a full chunk and we know
                #   more will come.
                if not self.buf:
                    trace('waiting for input')
                else:
                    trace('waiting for more input')
                t = time.time()
                self.condMoreInput.wait()
                t = time.time() -t
                trace('Got more input, wait took %.4fs' % t)
            if self.resetFlag:
                trace('resetting')
                self.resetFlag = 0
                self.writtenSamps = 0
                self.silentSamps = 0
                if self.dsp:
                    self.dsp.reset()
                    self.dsp.close()
                    self.dsp = None
                continue
            if self.pendingBuf:
                # If either we're not far enough to have worried about
                # finishing yet, or were completely done speaking the
                # previous utterance (means waiting for this to be true):
                if self.buf or not self.dsp:
                    if self.buf:
                        trace('Tacking pendingBuf on existing buf')
                    else:
                        trace('Restarting with pending buf')
                    self.buf += self.pendingBuf
                    self.pendingBuf = ''
                    self.finishFlag = self.pendingFinishFlag
                    self.pendingFinishFlag = 0
                    self.silentSamps = 0
            self._open()
            assert self.buf or self.finishFlag
            if self.finishFlag:
                b = self.buf + self.silence
            else:
                b = self.buf
            r = self._write(b)
            if self.resetFlag:
                continue
            br = min(r, len(self.buf))
            sr = r-br
            self.buf = self.buf[br:]
            self.writtenSamps += br/2
            self.silentSamps += sr/2
            if br:
                trace('wrote %d bytes' % br)
            if sr:
                trace('sent silence: %d bytes' % sr)
            buffed = self.dsp.obufcount()
            self.spokenSamps = self.writtenSamps \
                               - max(buffed -self.silentSamps, 0)
            trace('set spokenSamps %d' % self.spokenSamps)
            if not self.buf:
                if self.finishFlag:
                    if buffed <= self.silentSamps:
                        trace('graceful close')
                        self.dsp.reset()
                        self.dsp.close()
                        self.dsp = None
                elif buffed <= min(self.bufsize/4, self.rate/5):
                    # FIXME: Actually we probably don't get here: we're
                    # probably stuck waiting on condMoreInput.
                    trace('underrun mitigate')
                    self.dsp.sync()
                    self.dsp.close()
                    self.dsp = None

if 0 and __name__ == "__main__":
    s = SndOutput()
    import time
    turns = 0
    while 1:
        turns += 1
        b = sys.stdin.read(8192)
        if not b:
            break
        s.give(b)
        t = s.inputSleepTime()
        if t:
            trace('inputter sleeps %f' % t)
            time.sleep(t)
        if turns % 20 == 0:
            s.allGiven()
            trace('pause')
            time.sleep(9)
            s.reset()
    s.allGiven()
    time.sleep(10)
