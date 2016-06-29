
from collections import OrderedDict
import time
import json
import sys

# Representation of a data value category, with various properties
class DataType:
    def __init__(self, name, type=float, show=True, export_csv=True, units=None):
        # bool doesn't actually parse the value, just checks whether string is empty
        if type == bool:
            type = lambda x: x == "1" or x == "True"
        self.name = name
        self.type = type
        self.show = show
        self.export_csv = export_csv
        self.units = units

        self.full_name = self.name.replace("_", " ")
        if self.units:
            self.full_name += " (" + self.units + ")"

# Manages parsing incoming serial packets, recieving data in given data types, and passes it to
# listeners.  Also tracks system date and time.  
class Dispatcher:
    def __init__(self, *data_types):
        data_types = (DataType('sys date', str, False),
                      DataType('sys time', str, False),
                      DataType('log', str, False, False)) + data_types

        self.data_names = [d.name for d in data_types]
        self.data_types = {d.name: d for d in data_types}
        self.data = {name: None for name in self.data_names}
        self.time = {name: None for name in self.data_names}
        self.listeners = {name: [] for name in self.data_names}
        self.start_time = None
        self.current_line = ""

    def reset(self):
        self.start_time = None
        for ls in self.listeners.values():
            for l in ls:
                l[1] = 0

    def add_listener(self, name, fn, delay=0):
        self.listeners[name].append([delay, 0, fn])

    def acceptText(self, text, txtout=sys.stdout, errout=sys.stderr):
        lines = (self.current_line + text).split("\n")
        abs_time = None
        for line in lines[:-1]:
            line = line.strip("\r")
            if line.startswith("@@@@@") and line.endswith("&&&&&"):
                try:
                    data = OrderedDict([entry.split(':') for entry in line[5:][:-5].split(';')])
                    if '_time' in data and data['_time'] != "":
                        abs_time = int(data['_time'])
                    else:
                        abs_time = None
                    for name, value in data.items():
                        if name != '_time':
                            self.accept(name, abs_time, value, errout)
                    self.accept("sys date", abs_time, time.strftime("%d/%m/%Y"))
                    self.accept("sys time", abs_time, time.strftime("%H:%M:%S"))
                except ValueError:
                    print("Invalid packet", line, file=errout)
            else:
                print(line, file=txtout)
        if lines[-1].startswith("@"):
            self.current_line = lines[-1]
        else:
            print(lines[-1], end='', file=txtout)
            self.current_line = ""
        # Always update log, even if parse failed
        self.accept('log', abs_time, text, errout)
        
    def accept(self, name, time, value, errout=sys.stderr):
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
                print("Invalid value for", name, "recieved:", value, file=errout)

            for l in self.listeners[name]:
                delay, last, listener = l
                if time == None or time - last > delay or time < last:
                    listener(*self.request(name))
                    if time != None:
                        l[1] = time
            return True

    def request(self, name):
        return self.time[name], self.data[name]

# Manages the data for a spesific run.  Attatches handlers to a Dispatcher, logs the data when
# running, can save or load data runs in various formats.  Listeners can be attatched that trigger
# on new data when there is an active run
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
                    # If the time jumps backward (recieved a corrupted timestamp)
                    # overwrite the most recent data point
                    if (len(self.data[name][0]) > 0 and
                        (time < self.data[name][0][-1] or self.data[name][0][-1] < 0)):
                        self.data[name][0][-1] = time
                        self.data[name][1][-1] = value
                    else:
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
            data_names = [name
                          for name in self.dispatcher.data_names
                          if self.dispatcher.data_types[name].export_csv]
            result = "abs time," + ",".join(data_names) + "\n"
            data = OrderedDict()
            for name, (times, values) in self.data.items():
                if name in data_names:
                    for time, value in zip(times, values):
                        if time not in data:
                            data[time] = {}
                        data[time][name] = value
            for time, updates in data.items():
                result += (str(time) + "," +
                           ",".join(str(updates[n]) if n in updates else ""
                                    for n in data_names) + "\n")
            return result
        elif format == 'json':
            return json.dumps(list(self.data.items()))
        elif format == 'log':
            return "".join(self.request('log')[1])
        else:
            sys.exit("Unsupported format" + format)

    # txtout is stream to write non-packet text when loading a log
    def load(self, format, text, txtout=sys.stdout, errout=sys.stderr):
        if format == 'json':
            data = OrderedDict(json.loads(text))
            if set(self.data.keys()) != set(data.keys()):
                #sys.exit("Invalid fields")
                return False
            else:
                self.data = data
        elif format == 'csv':
            rows = [row.split(',') for row in text.split('\n')]
            data = [(name, ([], [])) for name in rows[0][1:]]
            for row in rows[1:]:
                for elem, (name, (time_elems, data_elems)) in zip(row[1:], data):
                    if elem != "":
                        elem = self.dispatcher.data_types[name].type(elem)
                        time_elems.append(int(row[0]))
                        data_elems.append(elem)
            self.data = OrderedDict(data)
        elif format == 'log':
            self.reset()
            self.start()
            self.dispatcher.acceptText(text, txtout, errout)
            self.stop()
        else:
            sys.exit("Unsupported format" + format)
        self.update_all_listeners(True)
        return True
