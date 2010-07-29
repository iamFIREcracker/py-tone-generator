#!/usr/bin/python
# -*- coding: Latin-1 -*-

"""Module containing an helper widget for the generation of tones.
"""

from __future__ import division
from math import log10

import gobject
import gtk
from gtk import gdk


class ToneGenerator(gtk.Window):
    """Widget used to generate pairs of frequencies and volume.
    
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
        super(ToneGenerator, self).__init__()

        self.connect('delete-event', self.delete_cb)
        
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

    def delete_cb(self, window, event):
        """Close the window and quit the mainloop.
        """
        gtk.main_quit()

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
        """Store the dimensions of the drawing area for future use.
        """
        return True
    
    def expose_cb(self, darea, event):
        """Redraw either the whole window or a part of it.
        """
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
        _, _, width, height = self.darea.get_allocation()
        
        scale_width = log10(20000) # between 1 and 20000
        scale_offset = 0 # start from 1
        v = (scale_width * x / width) + scale_offset
        freq = max(0, min(10 ** v, 20000))
        
        y = height - 1 - y
        scale_width = 2 # between 0.01 and 1
        scale_offset = -2 # start from 0.01
        v = (scale_width * y / height) + scale_offset 
        volume = max(0, min(10 ** v, 1))

        return freq, volume
