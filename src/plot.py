import math
import sys
from itertools import *

from matplotlib.gridspec import GridSpec

# Representation of a group of plotted data values
class Plot:
    def __init__(self, x, ys, name=None, ys_names=None, width=1, height=1, style=None, legend='best', show_x_label=True):
        self.x = x
        self.ys = [ys] if type(ys) == str else ys

        # Find a common suffix, if any, of the ys names
        suffix = ""
        for cs in zip(*map(reversed, self.ys)):
            # All chars are the same
            if cs[1:] == cs[:-1]:
                suffix = cs[0] + suffix
            else:
                break
        suffix = suffix.replace("_", " ")
        if " " in suffix:
            suffix = suffix[suffix.index(" "):]
        
        if ys_names:
            self.ys_names = ys_names
        elif suffix:
            # If the suffix exists, remove it from all ys names
            self.ys_names = [y[:len(y) - len(suffix)].replace("_", " ") for y in self.ys]
        else:
            self.ys_names = [y.replace("_", " ") for y in self.ys]

        if name != None:
            self.name = name
        elif len(self.ys) == 1:
            self.name = self.ys[0]
        elif suffix:
            self.name = suffix[1:]
        else:
            self.name = None

        self.width = width
        self.height = height
        self.style = style
        self.legend = legend
        self.show_x_label = show_x_label

        self.update = {y: ([], []) for y in self.ys}
        self.lines = {y: None for y in self.ys}

    def create(self, manager, fig, gs):
        data_types = manager.dispatcher.data_types
        self.subplot = fig.add_subplot(gs)
        if self.name:
            self.subplot.set_title(self.name)
        if self.show_x_label:
            if self.x == 'time':
                self.subplot.set_xlabel("time (sec)")
            else:
                self.subplot.set_xlabel(self.x + (" (" + data_types[self.x].units + ")" if data_types[self.x].units else ""))

        # Check plot datatypes are in manager datatypes
        for y in self.ys:
            if y not in data_types:
                raise AssertionError(y + " not in datatypes: " + str(data_types))

        ys_units = [data_types[y].units for y in self.ys]
        assert len(set(ys_units)) <= 1 # All units must be the same, if included
        if ys_units[0]:
            self.subplot.set_ylabel(ys_units[0])
        for i, y in enumerate(self.ys):
            y_name = self.ys_names[i] if self.ys_names[i] else data_types[y].full_name
            if self.style:
                self.lines[y], = self.subplot.plot([], [], self.style, label=y_name)
            else:
                self.lines[y], = self.subplot.plot([], [], label=y_name)
        if len(self.ys) > 1 and self.legend:
           self.subplot.legend(loc=self.legend)

        # Set up listeners
        max_points = 1000
        for y in self.ys:
            def fn(x_data, y_data, y=y):
                # If the x series is the time, then scale it to plot in seconds
                if self.x == 'time':
                    x_data = [x / 1000 for x in x_data]
                # If the x series isn't the time, then we need to request it and syncronyze it with the y data
                else:
                    y_times = x_data
                    x_times, x_data = manager.request(self.x)
                    assert len(x_data) == len(x_times)
                    assert len(y_data) == len(y_times)

                    # Walk through both lists, finding the largest set of matching data points with the closest times
                    i = 0
                    j = 0
                    new_x_data = []
                    new_y_data = []
                    last_x_time = None
                    last_y_time = None
                    while i < len(x_data) and j < len(y_data):
                        if x_times[i] != last_x_time and y_times[j] != last_y_time:
                            new_x_data.append(x_data[i])
                            new_y_data.append(y_data[j])
                            last_x_time = x_times[i]
                            last_y_time = y_times[j]
                        if x_times[i] < y_times[j]:
                            i += 1
                        elif x_times[i] > y_times[j]:
                            j += 1
                        else:
                            i += 1
                            j += 1
                    x_data = new_x_data
                    y_data = new_y_data
                        
                assert len(x_data) == len(y_data)
                # 'Prune' plotted data to avoid slow-down with large amounts of data
                indices = range(0, len(x_data), max(len(x_data) // max_points, 1))
                x_data = [x_data[i] for i in indices]
                y_data = [y_data[i] for i in indices]
                self.update[y] = x_data, y_data

            manager.add_listener(y, fn)

    def animate(self):
        updated = False
        for y in self.ys:
            if self.update[y]:
                x_data, y_data = self.update[y]
                self.update[y] = None
                self.lines[y].set_xdata(x_data)
                self.lines[y].set_ydata(y_data)
                updated = True
        if updated:
            self.subplot.relim()
            self.subplot.autoscale_view(None, True, True)

# Generate a layout for the given plots
def gen_layout(plots):
    # Minimum possible size based on number of plots
    for height in count(int(math.ceil(math.sqrt(len(plots))))):
        for width in (height - 1, height):
            # Table of open grid locations
            available = {(i, j): True
                         for i in range(width)
                         for j in range(height)}
            
            # List of info for each plot
            layout = []

            # Attempt to place each plot
            for plot in plots:
                # Attempt to find a location for the plot, breaking when successful
                for y, x in product(range(0, height - plot.height + 1), range(0, width - plot.width + 1)):
                    if all(available[i, j]
                           for i in range(x, x + plot.width)
                           for j in range(y, y + plot.height)):
                        break
                # No valid location, try the next grid size
                else:
                    break
                layout.append((x, x + plot.width, y, y + plot.height))
                for i in range(x, x + plot.width):
                    for j in range(y, y + plot.height):
                        available[i, j] = False
            # All plots were placed successfully (loop did not break)
            else:
                return width, height, layout

def setup(plots, fig, manager):
    width, height, layout = gen_layout(plots)
    gridspec = GridSpec(height, width)

    for plot, (x1, x2, y1, y2) in zip(plots, layout):
        plot.create(manager, fig, gridspec[y1:y2, x1:x2])

    if plots:
        fig.tight_layout(pad=2)
