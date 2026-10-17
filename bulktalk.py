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

# Takes text as input and either speaks out the audio directly through MBROLA,
# or with -o <outfile> dumps the audio to a file.
# NB: The filename is simply passed to MBROLA; MBROLA will choose the format
# according to the extension of the requested output file.

import sys, os

import setencoding
import ttp
import config

import tracing

def trace(msg):
    mod = 'wphons'
    tracing.trace(mod+': '+msg)

if __name__ == "__main__":
  setencoding.stdfilesEncoding(None,0,0)
  setencoding.decodeArgs()
  outf = None
  verbose = 0
  args = sys.argv[1:]

  while args and args[0][0] == '-':
    if len(args) >= 2 and args[0] == '-o':
      outf = args[1]
      args = args[2:]
    elif args[0] == '-v':
      verbose = 1
      args = args[1:]
    else:
      sys.stderr.write('Usage: %s [ -v ] [ -o <output_file> ] [ text... ]\n' \
                       % (sys.argv[0]))
      sys.stderr.write('( text can also be provided on standard input or interactively)\n')
      sys.exit(1)

  if args:
    text = ' '.join(args)
    interactive = False
  else:
    interactive = sys.stdin.isatty()
    if interactive:
      text = sys.stdin.readline()
    else:
      text = sys.stdin.read()
    text = text.decode(setencoding.get_file_encoding(sys.stdin))

  while text:
    phonos = ttp.process(text, verbose)[0]
    cmd = config.mbrola_prog_path \
          + " -f " + str(config.mbrola_f) \
          + " -t " + str(config.mbrola_t) \
          + " -e " + config.mbrola_voice \
          + " - " \
          + ( outf or "-.au | sox -t .au - -tossdsp "+config.snd_dev )
    pipe = os.popen(cmd, 'w')
    phonos = phonos.split('\n')
    phonos.insert(0, "_\t200")
    phonos.insert(-2, "_\t200")
    phonos = '\n'.join(phonos)
    pipe.write(phonos)
    pipe.flush()
    pipe.close()
    if interactive:
      text = sys.stdin.readline()
      text = text.decode(setencoding.get_file_encoding(sys.stdin))
    else:
      text = None
