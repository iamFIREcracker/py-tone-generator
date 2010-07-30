#!/usr/bin/python
# -*- coding: Latin-1 -*-

"""Module containing an helper widget for the generation of tones.
"""

from __future__ import division
from math import log10

import cairo
import gobject
import gst
import gtk
from gtk import gdk


class ToneGeneratorWidget(gtk.Window):
    """Widget used to generate pairs of frequencies and volume values.
    
    Create a drawing area connected to mouse events. Depending on the position
    of the mouse inside the drawing area, the values of frequency and volume
    are computed and emitted.
    """
    
    __gsignals__ = {
            'start-tone': (gobject.SIGNAL_RUN_FIRST, None, ()),
            'tone-value': (gobject.SIGNAL_RUN_FIRST, None,
                (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)),
            'end-tone': (gobject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self):
        """Constructor.
        
        Create a drawing area and connect to mouse events.
        """
        super(ToneGeneratorWidget, self).__init__()

        self.freq = (100, 10000)
        self.volume = (0.01, 1)
        
        self.darea = gtk.DrawingArea()
        self.darea.add_events(gdk.BUTTON_PRESS_MASK
                              | gdk.BUTTON_RELEASE_MASK
                              | gdk.POINTER_MOTION_MASK
                              | gdk.POINTER_MOTION_HINT_MASK)
        self.darea.connect('button-press-event', self.button_press_cb)
        self.darea.connect('button-release-event', self.button_release_cb)
        self.darea.connect('configure-event', self.configure_cb)
        self.darea.connect('expose-event', self.expose_cb)
        self.darea.connect('motion_notify_event', self.motion_notify_cb)
        self.add(self.darea)
        self.show_all()

    def button_press_cb(self, darea, event):
        """Start gstreamer pipeline.
        
        Set the values of frequency and volume depending on the position of
        the mouse.
        """
        x = event.x
        y = event.y
        freq, volume = self.coords_to_settings(x, y)
        self.emit('tone-value', freq, volume)
        self.emit('start-tone')
        return True

    def button_release_cb(self, darea, event):
        """Stop gstreamer pipeline.
        """
        self.emit('end-tone')
        return True

    def configure_cb(self, darea, event):
        """Update the cairo context used for the drawing actions.
        """
        width, height = darea.window.get_size()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.cr = cairo.Context(self.surface)
        self.draw_grid(self.cr, width, height)
        return True
    
    def expose_cb(self, darea, event):
        """Redraw either the whole window or a part of it.
        """
        cr = darea.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                     event.area.width, event.area.height)
        cr.clip()
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()
        return False
    
    def motion_notify_cb(self, darea, event):
        """Change the frequency and the volume of the generated sound depending
        on the mouse position inside the window.
        """
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
        if state & gdk.BUTTON1_MASK or state & gdk.BUTTON3_MASK:
            freq, volume = self.coords_to_settings(x, y)
            self.emit('tone-value', freq, volume)
        return True

    def draw_grid(self, cr, width, height):
        """Draw a grid with values of frequency and volume.
        
        Keywords:
            cr cairo context used for drawing operations.
        """
        # portrait
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, width, height)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()
        
        # grid
        f_min, f_max = self.freq
        v_min, v_max = self.volume
        cr.set_dash([1.0, 1.0])
        cr.set_line_width(1.0)
        for i in xrange(10):
            norm_x = i / 10
            norm_y = i / 10
            x = int((1 - norm_x) * width)
            y = int(norm_y * height)
            
            #  horizontal lines
            cr.move_to(0, y + 0.5)
            cr.rel_line_to(width - 1, 0)
            cr.stroke()
            
            # vertical lines
            cr.move_to(x + 0.5, 0)
            cr.rel_line_to(0, height - 1)
            cr.stroke()
            
            # volume labels
            exp = (1 - norm_y) * (log10(v_max) - log10(v_min)) + log10(v_min)
            text = str(int(10 ** (exp + 2))) + '%'
            _, _, _, t_height, _, _ = cr.text_extents(text)
            cr.move_to(2, 2 + y + t_height)
            cr.show_text(text)
            
            # freq labels
            exp = (1 - norm_x) * (log10(f_max) - log10(f_min)) + log10(f_min)
            text = str(int(10 ** exp)) + 'Hz'
            _, _, t_width, _, _, _ = cr.text_extents(text)
            cr.move_to(-2 + x - t_width, -2 + height)
            cr.show_text(text)

    def coords_to_settings(self, x, y):
        """Convert given coordinate to volume and frequency.
        
        Higher values of x correspond to high values of frequencies.
        Lower values of y correspond to high values of volume (In device space
        y = 0 is placed on top of the window).
        
        Keywords:
            x X position of the mouse.
            y Y position of the mouse.
            
        Return:
            Pair of frequency and volume values.
        """
        width, height = self.darea.window.get_size()
        
        f_min, f_max = self.freq
        scale_width = log10(f_max) - log10(f_min)
        scale_offset = log10(f_min)
        v = (scale_width * x / width) + scale_offset
        freq = max(f_min, min(10 ** v, f_max))
        
        y = height - 1 - y
        v_min, v_max = self.volume
        scale_width = log10(v_max) - log10(v_min)
        scale_offset = log10(v_min)
        v = (scale_width * y / height) + scale_offset 
        volume = max(v_min, min(10 ** v, v_max))

        return freq, volume
    
class GstToneGenerator(object):
    """Gstreamer based tone generator.
    """
    
    def __init__(self):
        """Constructor.
        """
        str_pipe = '''audiotestsrc name=source !
                      autoaudiosink'''
        self.pipeline = gst.parse_launch(str_pipe)
        self.source = self.pipeline.get_by_name('source')

    def start(self):
        """Start emitting sounds.
        """
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    def stop(self):
        """Stop emitting sounds.
        """
        self.pipeline.set_state(gst.STATE_NULL)
        
    def set_values(self, freq, volume):
        """Change the frequency and volume values of the sound source.
        
        Keywords:
            freq frequency value between 0 and 20k.
            volume volume value between 0 and 1.
        """
        self.source.set_property('freq', max(0, min(freq, 20000)))
        self.source.set_property('volume', max(0, min(volume, 1)))
