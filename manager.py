
from collections import OrderedDict
import time
import json
import sys
import matplotlib

class DataType:
    def __init__(self, name, type=float, plot=True, units=None):
        self.name = name
        self.type = type
        self.plot = plot
        self.units = units

class DataManager:
    def __init__(self, *data_types):
        self.data_names = [d.name for d in data_types]
        self.data_types = {d.name: d for d in data_types}
        self.data = OrderedDict((name, ([], [])) for name in self.data_names)
        self.listeners = {name: [] for name in self.data_names}
        self.needs_update = {name: False for name in self.data_names}
        self.running = False

    def add_listener(self, name, fn):
        self.listeners[name].append(fn)

    def update_listeners(self, name):
        self.needs_update[name] = False
        times, values = self.request(name)
        for listener in self.listeners[name]:
            listener(times, values)

    def update_all_listeners(self):
        for name in self.data_types:
            if self.needs_update[name]:
                self.update_listeners(name)

    def update_one_listener(self):
        for name in self.data_types:
            if self.needs_update[name]:
                self.update_listeners(name)
                break

    def force_update_all_listeners(self):
        for name in self.data_types:
            self.update_listeners(name)    

    def start(self):
        self.running = True
        self.start_time = None
        self.force_update_all_listeners()

    def stop(self):
        self.running = False
        self.force_update_all_listeners()

    def reset(self):
        for times, values in self.data.values():
            times.clear()
            values.clear()
        self.running = False
        self.force_update_all_listeners()

    def accept(self, name, time, value):
        if not self.running:
            print("Data manager is not running, cannot accept new data")
            return False
        elif name not in self.data_types:
            print("Received unrecognized data type", name)
            return False
        else:
            if self.start_time == None:
                self.start_time = time
                time = 0
            else:
                time -= self.start_time
            try:
                self.data[name][1].append(self.data_types[name].type(value))
                self.data[name][0].append(time)
            except ValueError:
                print("Invalid value for", name, "recieved:", value)
            self.needs_update[name] = True
            return True

    def request(self, name):
        return self.data[name]

    def dump(self, format):
        if format == 'csv':
            result = "time," + ",".join(self.data_names) + "\n"
            data = {}
            for name, (times, values) in self.data.items():
                for time, value in zip(times, values):
                    if time not in data:
                        data[time] = {}
                    data[time][name] = value
            current_vals = {name: None for name in self.data_names}
            for time, updates in sorted(data.items()):
                for name, update in updates.items():
                    current_vals[name] = update
                result += (str(time) +
                           "," +
                           ",".join(str(current_vals[n])
                                    if current_vals[n] != None
                                    else "" for n in self.data_names) + "\n")
            return result
        elif format == 'json':
            return json.dumps(list(self.data.items()))
        else:
            sys.exit("Unsupported format", format)

    def load(self, format, text):
        if format == 'json':
            self.data = OrderedDict(json.loads(text))
        else:
            sys.exit("Unsupported format", format)
        self.force_update_all_listeners()
