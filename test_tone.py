#!/usr/bin/python
# -*- coding: Latin-1 -*-

import gobject
import gst
import gtk

from tone import GstToneGenerator


if __name__ == '__main__':
    str_pipe = '''audiotestsrc name=source !
                  autoaudiosink'''
    pipeline = gst.parse_launch(str_pipe)

    tone = GstToneGenerator(pipeline, pipeline.get_by_name('source'))
    
    gobject.threads_init()
    gtk.main()