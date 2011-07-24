#!/usr/bin/python2

import pygtk
import gtk, gobject, cairo
from gtk import gdk
import math
import random
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

        self.colors = [(1,1,1), (0,0,0)]
        self.screen = screen
        screen.addDoodad(self)
        self.frame = 0

    def draw(self, cr):
        cr.save()
        cr.translate(10,10)

        for y in range(self.h):
            cr.save()
            for x in range(self.w):
                cr.set_source_rgb(*self.colors[self.grid[x][y]])
                cr.rectangle(0, 0, Grid.cell_size, Grid.cell_size)
                cr.fill()
                cr.translate(Grid.cell_size, 0)

            cr.restore()
            cr.translate(0, Grid.cell_size)

        cr.restore()

    def tick(self):
        self.frame += 1

class Water(Grid):
    """Simple water automata."""

    def __init__(self, screen, w, h):
        super(Water, self).__init__(screen, w, h)
        # 0: air, 1: water, 2: wall
        # 3: source, 4: sink
        self.colors = [(1,1,1), (0,0,1), (0,0,0), (0,0,0.7), (1,0,0)]

        for _ in range(int(self.w * self.h * 0.75)):
            x = int(random.random()*(self.w-2))+1
            y = int(random.random()*(self.h-2))+1
            k = random.random()

            if k > 0.7:
                self.grid[x][y] = 2
            elif x <= self.w - 20:
                self.grid[x][y] = 1

        # place some sources on top
        for _ in range(int(self.w * 0.25)):
            x = int(random.random() * (self.w-2) + 1)
            self.grid[x][1] = 3

        # Cover the bottom in sinks
        for _ in range(int(self.w * 0.15)):
            x = int(random.random() * (self.w-20) + 1)
            self.grid[x][-2] = 4

        # Build the walls
        for x in range(self.w):
            self.grid[x][0] = 2
            self.grid[x][-1] = 2
        for y in range(self.h):
            self.grid[0][y] = 2
            self.grid[-1][y] = 2
            self.grid[-20][y] = 2

    def tick(self):
        super(Water, self).tick()

        processors = {
            0: self.cell_static,
            1: self.cell_water,
            2: self.cell_static,
            3: self.cell_source,
            4: self.cell_sink,
        }
        # iterate from the bottom to the top
        for y in range(self.h-2, 0, -1):
            for x in range(1,self.w-1):
                processors[self.grid[x][y]](x,y)

    def cell_static(self, x, y):
        pass

    def cell_source(self, x, y):
        if self.grid[x][y+1] == 0: # air
            if random.random() > 0.5:
                self.grid[x][y+1] = 1

    def cell_sink(self, x, y):
        if self.grid[x][y-1] == 1:
            self.grid[x][y-1] = 0
        if self.grid[x+1][y] == 1:
            self.grid[x+1][y] = 0
        if self.grid[x-1][y] == 1:
            self.grid[x-1][y] = 0

    def cell_water(self, x, y):
        # Fall straight down
        if self.grid[x][y+1] == 0:
            self.grid[x][y] = 0
            self.grid[x][y+1] = 1
            return

        fall_choice = []
        # Fall down and to the side
        if self.grid[x-1][y+1] == 0:
            fall_choice.append((x-1,y+1))
        if self.grid[x+1][y+1] == 0:
            fall_choice.append((x+1,y+1))

        # Roll towards a fall
        if x > 1 and self.grid[x-1][y+1] != 0 and self.grid[x-2][y+1] == 0:
            fall_choice.append((x-1,y))
        if x < self.w - 2 and self.grid[x+1][y+1] != 0 and self.grid[x+2][y+1] == 0 and self.grid[x+1][y] == 0:
            fall_choice.append((x+1,y))

        if len(fall_choice) > 0:
            x_, y_ = random.choice(fall_choice)
            self.grid[x][y] = 0
            self.grid[x_][y_] = 1
            return

        # len(fall_choice) == 0
        # Make staying in place possible.
        fall_choice.append((x,y))
        if self.grid[x-1][y] == 0:
            fall_choice.append((x-1,y))
        if self.grid[x+1][y] == 0:
            fall_choice.append((x+1,y))

        x_, y_ = random.choice(fall_choice)
        self.grid[x][y] = 0
        self.grid[x_][y_] = 1

class GOL(Grid):
    """Game of life. Kind of slow."""

    def __init__(self, screen, w, h):
        super(GOL, self).__init__(screen, w, h)
        for _ in range(int(self.w * self.h * 0.5)):
            x = int(random()*(self.w-2))+1
            y = int(random()*(self.h-2))+1
            self.grid[x][y] = 1

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

    Water(widget, 100, 100)

    widget.show()
    window.add(widget)
    window.present()

    gtk.main()

if __name__ == '__main__':
    run(Screen, 200)
