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

# Test for regressions in the Text to phoneme engine.

import sys, re

import setencoding
import ttp
import config

setencoding.stdfilesEncoding()

f = file(config.testfile, "r")
regressions = 0
checks = 0

# remove coments, extra blanks, end of line, etc.
cleanup = re.compile( r"\s+#.*|(?<!\\)#.*|\s*\n" )

# a string -> phonemes association entry
entry = re.compile( r"^\s*(.+?)\s+\-\>\s+(.+)$" )

for ln,line in enumerate(f):
    line = line.decode('utf8')
    line = cleanup.sub("", line)
    if not line: continue
    m = entry.match(line)
    if m:
        string, pho_list = m.groups()
        pho_result = ttp.word2phons(string)
        if pho_list != pho_result:
            print "Regression found: (line %d) \"%s\"" % (ln+1, string)
            print "Expected: %s\nObtained: %s\n" % (pho_list, pho_result)
            regressions += 1
        checks += 1
        continue
    sys.stderr.write('%s (%d): syntax error:\n%s\n' % (config.testfile, ln+1, line))
    sys.exit(1)

print("%d regression%s found in %d checks"
      % (regressions, regressions > 1 and "s" or "", checks))

