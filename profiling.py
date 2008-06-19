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

import time

_prof_records = {}

def profPut(name, time):
    oldt = _prof_records.get(name, 0)
    _prof_records[name] = oldt +time

class ProfProxy:
    def __init__(self, name, func):
        self.name = name
        self.func = func
    def __call__(self, *args, **kwargs):
        t = time.time()
        r = self.func(*args, **kwargs)
        profPut(self.name, time.time() -t)
        return r

class ProfMonitor:
    def __init__(self, name):
        self.name = name
        self.startTime = time.time()
    def __invert__(self):
        t = time.time() -self.startTime
        profPut(self.name, t)
        self.startTime = None # So it's not used a second time

def profReport():
    keys = _prof_records.keys()
    keys.sort()
    out = [(name, _prof_records[name]) for name in keys]
    out = [('%-20s: %.4fs' % (name, val)) for name,val in out]
    out = '\n'.join(out)
    return out
