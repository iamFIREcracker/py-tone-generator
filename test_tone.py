#!/usr/bin/python
# -*- coding: Latin-1 -*-

import gobject
import gst
import gtk

from tone import ToneGenerator

    
class GstToneGenerator(ToneGenerator):
    """Gstreamer based tone generator.
    
    Extend the base class ToneGenerator in order to control both the given
    pipeline and source element with emitted signals.
    """
    
    def __init__(self, pipeline, source):
        """Constructor.
        
        Store the pipeline locally.
        
        Keywords:
            pipeline gstreamer pipeline.
            source element used to generate sounds.
        """
        super(GstToneGenerator, self).__init__()
        self.connect('end-tone', self.end_tone_cb)
        self.connect('start-tone', self.start_tone_cb)
        self.connect('tone-value', self.tone_value_cb)
        
        self.pipeline = pipeline
        self.source = source
        
    def end_tone_cb(self, widget):
        """Stop the pipeline.
        """
        self.pipeline.set_state(gst.STATE_NULL)
        
    def start_tone_cb(self, widget):
        """Start the pipeline.
        
        This method will make the pipeline to start reproducing sounds.
        """
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def tone_value_cb(self, widget, freq, volume):
        """Change the values of frequency and volume with the given ones.
        """
        self.source.set_property('freq', freq)
        self.source.set_property('volume', volume)


if __name__ == '__main__':
    str_pipe = '''audiotestsrc name=source !
                  autoaudiosink'''
    pipeline = gst.parse_launch(str_pipe)

    tone = GstToneGenerator(pipeline, pipeline.get_by_name('source'))
    
    gobject.threads_init()
    gtk.main()
