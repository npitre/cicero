#!/usr/bin/python
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

# This is an executable script that will invoke the tts configured to
# expect communication using the BRLTTY ExternalSpeech protocol.

import app_brltty_es, main

if __name__ == "__main__":
    s = main.SpeechServ(app_brltty_es.AppFeed)
    s.run()
