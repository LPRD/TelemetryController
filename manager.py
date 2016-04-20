
from collections import OrderedDict
import time
import json
import sys
#import matplotlib

class DataType:
    def __init__(self, name, type=float, plot=False, show=True, units=None):
        # bool doesn't actually parse the value, just checks whether string is empty
        if type == bool:
            type = lambda x: x == "1" or x == "True"
        self.name = name
        self.type = type
        self.plot = plot
        self.show = show
        self.units = units

class Dispatcher:
    def __init__(self, *data_types):
        data_types = (DataType('sys date', str, False, False), DataType('sys time', str, False, False)) + data_types

        self.data_names = [d.name for d in data_types]
        self.data_types = {d.name: d for d in data_types}
        self.data = {name: None for name in self.data_names}
        self.time = {name: None for name in self.data_names}
        self.listeners = {name: [] for name in self.data_names}
        self.start_time = None

    def reset(self):
        self.start_time = None
        for ls in self.listeners.values():
            for l in ls:
                l[1] = 0

    def add_listener(self, name, fn, delay=0):
        self.listeners[name].append([delay, 0, fn])

    def accept(self, name, in_time, value):
        assert self._accept("sys date", in_time, time.strftime("%d/%m/%Y"))
        assert self._accept("sys time", in_time, time.strftime("%H:%M:%S"))
        return self._accept(name, in_time, value)
        
    def _accept(self, name, time, value):
        if name not in self.data_types:
            print("Received unrecognized data type", name)
            return False
        else:
            if time != None:
                if self.start_time == None:
                    self.start_time = time
                    time = 0
                else:
                    time -= self.start_time
            try:
                self.data[name] = self.data_types[name].type(value)
                self.time[name] = time
            except ValueError:
                print("Invalid value for", name, "recieved:", value)

            for l in self.listeners[name]:
                delay, last, listener = l
                if time == None or time - last > delay:
                    listener(*self.request(name))
                    if time != None:
                        l[1] = time
            return True

    def request(self, name):
        return self.time[name], self.data[name]

class DataManager:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.data = OrderedDict((name, ([], [])) for name in dispatcher.data_names)
        self.listeners = {name: [] for name in dispatcher.data_names}
        self.needs_update = {name: False for name in dispatcher.data_names}
        self.running = False

        for name in dispatcher.data_names:
            def fn(time, value, name=name):
                if self.running and time != None:
                    self.data[name][0].append(time)
                    self.data[name][1].append(value)
                    self.needs_update[name] = True
            dispatcher.add_listener(name, fn)

    def add_listener(self, name, fn):
        self.listeners[name].append(fn)

    def update_listeners(self, name):
        self.needs_update[name] = False
        times, values = self.request(name)
        for listener in self.listeners[name]:
            listener(times, values)

    def update_all_listeners(self, force=False):
        updated = False
        for name in self.dispatcher.data_types:
            if self.needs_update[name] or force:
                self.update_listeners(name)
                updated = True
        return updated

    def request(self, name):
        return self.data[name]

    def start(self):
        self.dispatcher.reset()
        self.running = True
        self.update_all_listeners(True)

    def stop(self):
        self.running = False
        self.update_all_listeners(True)

    def reset(self):
        for times, values in self.data.values():
            times.clear()
            values.clear()
        self.running = False
        self.update_all_listeners(True)

    def dump(self, format):
        if format == 'csv':
            result = "abs time," + ",".join(self.dispatcher.data_names) + "\n"
            data = {}
            for name, (times, values) in self.data.items():
                for time, value in zip(times, values):
                    if time not in data:
                        data[time] = {}
                    data[time][name] = value
            current_vals = {name: None for name in self.dispatcher.data_names}
            for time, updates in sorted(data.items()):
                for name, update in updates.items():
                    current_vals[name] = update
                result += (str(time) +
                           "," +
                           ",".join(str(current_vals[n])
                                    if current_vals[n] != None
                                    else "" for n in self.dispatcher.data_names) + "\n")
            return result
        elif format == 'json':
            return json.dumps(list(self.data.items()))
        else:
            sys.exit("Unsupported format" + format)

    def load(self, format, text):
        if format == 'json':
            data = OrderedDict(json.loads(text))
            if set(self.data.keys()) != set(data.keys()):
                #sys.exit("Invalid fields")
                return False
            else:
                self.data = data
        elif format == 'csv': # TODO: in progress
            rows = [row.split(',') for row in text.split('\n')]
            data = [(name, ([], [])) for name in rows[0]]
            last_row = ["" for elem in rows[0]]
            for row in rows[1:]:
                for i, elem in enumerate(row):
                    if elem != last_row[i]:
                        if data[i][0] not in ['abs time', 'sys data', 'sys time']:
                            elem = self.dispatcher.data_types[data[i][0]].type(elem)
                        if data[i][0] != 'abs time':
                            data[i][1][0].append(int(row[0]))
                            data[i][1][1].append(elem)
                last_row = row
            data = OrderedDict(data)
        else:
            sys.exit("Unsupported format" + format)
        self.update_all_listeners(True)
        return True
