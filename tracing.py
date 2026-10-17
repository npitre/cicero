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

# Simplistic debugging utility.
# TODO: Debugging/tracing levels or channels.

import sys, time

import config

_start = time.time()

def trace(msg):
    elapsed = time.time() - _start
    if type(msg) != type(u''):
        msg = str(msg)
    sys.stderr.write(('tr %.3f: ' % elapsed)+msg+'\n')
    sys.stderr.flush()

def trace_noop(ms):
    pass
if not config.tracing:
    trace = trace_noop
