#!/usr/bin/python
# -*- coding: Latin-1 -*-

import gobject
import gst
import gtk

from tone import GstToneGenerator
from tone import ToneGeneratorWidget


if __name__ == '__main__':
    def end_tone_cb(widget, tone_gen):
        tone_gen.stop()
        
    def start_tone_cb(widget, tone_gen):
        tone_gen.start()
        
    def tone_value_cb(widget, freq, volume, tone_gen):
        tone_gen.set_values(freq, volume)
        
    tone_gen = GstToneGenerator()
    
    tone_wid = ToneGeneratorWidget()
    tone_wid.connect('end-tone', end_tone_cb, tone_gen)
    tone_wid.connect('start-tone', start_tone_cb, tone_gen)
    tone_wid.connect('tone-value', tone_value_cb, tone_gen)
    
    gobject.threads_init()
    gtk.main()