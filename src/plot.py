

# Representation of a group of plotted data values
class Plot:
    def __init__(self, x, ys, name=None, style=None):
        self.x = x
        self.ys = [ys] if type(ys) == str else ys
        if len(self.ys) == 1 and name == None:
            name = self.ys[0]
        self.name = name
        self.style = style

        self.update = {y: ([], []) for y in self.ys}
        self.lines = {y: None for y in self.ys}

    def create(self, manager, fig, width, height, i):
        data_types = manager.dispatcher.data_types
        self.subplot = fig.add_subplot(width, height, i + 1)
        if self.name:
            self.subplot.set_title(self.name)
        if self.x == 'time':
            self.subplot.set_xlabel("time (sec)")
        else:
            self.subplot.set_xlabel(self.x + (" (" + data_types[self.x].units + ")" if data_types[self.x].units else ""))

        ys_units = [data_types[y].units for y in self.ys]
        assert len(set(ys_units)) <= 1 # All units must be the same, if included
        if ys_units[0]:
            self.subplot.set_ylabel(ys_units[0])
        for y in self.ys:
            if self.style:
                self.lines[y], = self.subplot.plot([], [], self.style, label=y)
            else:
                self.lines[y], = self.subplot.plot([], [], label=y)
        if len(self.ys) > 1:
           self.subplot.legend(loc='lower right')

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
                print("update", self.x, y, x_data, y_data)
                self.update[y] = None
                self.lines[y].set_xdata(x_data)
                self.lines[y].set_ydata(y_data)
                updated = True
        if updated:
            self.subplot.relim()
            self.subplot.autoscale_view(None, True, True)
