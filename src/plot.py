

# Representation of a group of plotted data values
class Plot:
    def __init__(self, x, ys, name=None):
        self.x = x
        self.ys = [ys] if type(ys) == str else ys
        if len(self.ys) == 1 and name == None:
            name = self.ys[0]
        self.name = name

    def setup_listeners(self, manager, update):
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
                update[self, y] = x_data, y_data

            manager.add_listener(y, fn)
