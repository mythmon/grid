#!/usr/bin/python2

import pygtk
import gtk, gobject, cairo
from gtk import gdk
import math
from random import random
from time import time

class Screen(gtk.DrawingArea):
    """ This class is a Drawing Area"""
    def __init__(self, w, h, speed):
        super( Screen, self ).__init__( )
        ## Connect events
        self.connect ( "expose_event", self.do_expose_event )

        # Frame caller
        gobject.timeout_add( speed, self.tick ) # Go call tick every 'speed' whatsits.

        self.width, self.height = w, h
        self.set_size_request (w, h)
        self.mousex, self.mousey = None, None

        self.doodads = []

    def tick(self):
        """This invalidates the screen, causing the expose event to fire."""
        if self.window == None:
            return True

        self.alloc = self.get_allocation()
        rect = gtk.gdk.Rectangle (0, 0, self.width, self.height)
        self.window.invalidate_rect ( rect, True )

        for d in self.doodads:
            d.tick()

        #self.do_expose_event(self.window, None)
        self.queue_draw()
        return True # Causes timeout to tick again.

    def draw(self):
        # screen is cleared automatically
        for d in self.doodads:
            d.draw(self.cr)

    def do_expose_event(self, widget, event):
        """The screen needs redrawn."""
        self.cr = self.window.cairo_create()
        self.draw()

    def addDoodad(self, d):
        self.doodads.append(d)

class Doodad(object):
    """Base class for drawables"""

    def __init__(self):
        pass

    def tick(self):
        pass

    def draw(self, cr):
        pass

class Grid(Doodad):
    """A base for cellular automata."""

    cell_size = 5

    def __init__(self, screen, w=25, h=25):
        # Make a  grid of zeros.
        self.w, self.h = w, h
        self.grid = [[0] * self.h for _ in range(self.w)]
        for _ in range(int(self.w * self.h * 0.5)):
            x = int(random()*self.w)
            y = int(random()*self.h)
            self.grid[x][y] = 1

        self.screen = screen
        screen.addDoodad(self)

    def draw(self, cr):
        cr.save()
        cr.translate(10,10)

        pix_w = Grid.cell_size * self.w
        pix_h = Grid.cell_size * self.h
        live_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, pix_w, pix_h)
        dead_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, pix_w, pix_h)
        live_cr = cairo.Context(live_surf)
        dead_cr = cairo.Context(dead_surf)

        live_cr.set_source_rgb(0,0,0)
        dead_cr.set_source_rgb(1,1,1)

        for y in range(self.h):
            for x in range(self.w):
                if self.grid[x][y] == 1:
                    live_cr.rectangle(0, 0, Grid.cell_size - 1, Grid.cell_size - 1)
                else:
                    dead_cr.rectangle(0, 0, Grid.cell_size - 1, Grid.cell_size - 1)

                live_cr.translate(Grid.cell_size, 0)
                dead_cr.translate(Grid.cell_size, 0)

            live_cr.translate(Grid.cell_size * self.w * -1, Grid.cell_size)
            dead_cr.translate(Grid.cell_size * self.w * -1, Grid.cell_size)
        live_cr.fill()
        dead_cr.fill()

        cr.rectangle(0,0,pix_w,pix_h)
        cr.set_source_surface(live_surf)
        cr.fill_preserve()
        cr.set_source_surface(dead_surf)
        cr.fill_preserve()

        cr.restore()

    def tick(self):
        if self.grid[0][0] == 0:
            self.grid[0][0] = 1
        else:
            self.grid[0][0] = 0

class GOL(Grid):

    def __init__(self, screen, w, h):
        super(GOL, self).__init__(screen, w, h)
        for x in range(w):
            self.grid[x][0] = 0
            self.grid[x][h-1] = 0
        for y in range(h):
            self.grid[0][y] = 0
            self.grid[w-1][y] = 0

    def tick(self):
        grid_copy = [row[:] for row in self.grid]

        for y in range(1,self.h-1):
            for x in range(1,self.w-1):
                # If the cell is alive, it will be a one. This counts neighbors.
                count = sum([self.grid[x-1][y-1], self.grid[x][y-1], self.grid[x+1][y-1],
                             self.grid[x-1][y],                      self.grid[x+1][y],
                             self.grid[x-1][y+1], self.grid[x][y+1], self.grid[x+1][y+1]])

                if self.grid[x][y] == 1 and not (2 <= count <= 3):
                    # Cell dies
                    grid_copy[x][y] = 0
                if self.grid[x][y] == 0 and count == 3:
                    # Cell is born
                    grid_copy[x][y] = 1

        self.grid = grid_copy

def run( Widget, speed ):
    window = gtk.Window( )
    window.maximize()
    w, h, = window.get_size()

    window.connect( "delete-event", gtk.main_quit )
    widget = Widget( w, h, speed )

    GOL(widget, 100, 100)

    widget.show()
    window.add(widget)
    window.present()

    gtk.main()

if __name__ == '__main__':
    run(Screen, 200)
