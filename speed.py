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

# Simplistic phonetization speed benchmark

f = open('top10000fr.txt','r')
lines = f.readlines()
# first 30 words. Simulates a 15word sentence.
lines = lines[:30]
txt = ' '.join([l.strip() for l in lines])
import ttp
import time
t = time.time()
# total time for 300 repeats
for i in xrange(600):
    out, indexes = ttp.process(txt)
t = time.time() -t
print 'took %fs' % t
