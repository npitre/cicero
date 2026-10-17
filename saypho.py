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

# Takes a list of phonemes as input and uses mbrola and sox to speak them out.


import sys, os

import setencoding
import config
import ttp

if __name__ == "__main__":
    setencoding.stdfilesEncoding()
    setencoding.decodeArgs()
    cmd = config.mbrola_prog_path \
          + " -f " + str(config.mbrola_f) \
          + " -t " + str(config.mbrola_t) \
          + " -e " + config.mbrola_voice \
          + " - -.raw | sox -traw -r16000 -c1 -w -s - -tossdsp " + config.snd_dev
    pipe = os.popen(cmd, 'w')

    phos = sys.argv[1:]
    if len(phos) == 1:
        phos = phos[0].split()
    out = ttp.phons2mbrola(phos)
    out = out.split('\n')
    out.insert(0, "_\t200")
    out.insert(-2, "_\t200")
    out = '\n'.join(out)
    print out
    pipe.write(out)
    pipe.flush()
