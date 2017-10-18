
from collections import OrderedDict
import time
import json
import sys

from typing import cast, Any, Union, List, Tuple, NamedTuple, Dict, Callable, Iterable, Sequence
from typing.io import TextIO

# Data handling functions

# Parse a string to get a value of a given type
def parse(type: type, value: str):
    # bool doesn't actually parse the value, just checks whether string is empty
    if type is bool:
        return value == "1" or value == "True"
    else:
        return type(value)

# Convert a value to a string that we can send
def unparse(value) -> str:
    # Treat bools as ints
    if type(value) is bool:
        value = int(value)
    return str(value)

# Representation of a data value category, with various properties
class DataType:
    def __init__(self,
                 name:       str,
                 type:       type = float,
                 show:       bool = True,
                 one_line:   bool = True,
                 export_csv: bool = False,
                 units:      str  = None) -> None:
        self.name = name
        self.type = type
        # bool doesn't actually parse the value, just checks whether string is empty
        self.parse = lambda value: parse(type, value)
        self.show = show
        self.one_line = one_line
        self.export_csv = export_csv
        self.units = units

        self.full_name = self.name.replace("_", " ")
        if self.units:
            self.full_name += " (" + self.units + ")"

# Representation of a serial packet that contains multiple data types
class PacketSpec:
    def __init__(self, name: str, *data_types: DataType) -> None:
        self.name = name
        self.data_types = data_types

Spec = Union[PacketSpec, DataType]
Data = Union[int, float, str]
DispatchListener = Callable[[int, Data], None]

# Manages parsing incoming serial packets, recieving data in given data types, and passes it to
# listeners.  Also tracks system date and time.  
class Dispatcher:
    def __init__(self, *specs: Spec) -> None:
        specs += (DataType('sys date', str, False),
                  DataType('sys time', str, False),
                  DataType('log', str, False, False))
        data_types = tuple(s for s in specs if isinstance(s, DataType))

        self.packet_specs = OrderedDict((s.name, s) for s in specs)
        self.data_names = [d.name for d in data_types]
        self.data_types = OrderedDict((d.name, d) for d in data_types)
        self.data = {name: None for name in self.data_names} # type: Dict[str, Data]
        self.time = {name: None for name in self.data_names} # type: Dict[str, int]
        self.listeners = {name: [] for name in self.data_names} # type: Dict[str, List[Tuple[DispatchListener, int]]]
        self.listener_last_updates = {name: [] for name in self.data_names} # type: Dict[str, List[int]]
        self.start_time = None # type: int
        self.current_line = ""

    def reset(self):
        self.start_time = None
        for name in self.data_names:
            for i in range(len(self.listener_last_updates[name])):
                self.listener_last_updates[name][i] = 0

    def add_listener(self, name: str, fn: DispatchListener, period=0):
        self.listeners[name].append((fn, period))
        self.listener_last_updates[name].append(0)

    def acceptText(self,
                   text: str,
                   txtout: TextIO = sys.stdout,
                   errout: TextIO = sys.stderr):
        # Split the unparsed text from previously with the new text into lines
        lines = (self.current_line + text).split("\n")

        # Parse each line as a packet or text output
        abs_time = None
        for line in lines[:-1]:
            line = line.strip("\r")

            # If line is a packet, parse it as such
            if line.startswith("@@@@@") and line.endswith("&&&&&"):
                try:
                    entries = (entry.split(':') for entry in line[5:][:-5].split(';'))
                    data = OrderedDict(((entry[0], entry[1].split(',')) for entry in entries))
                    if '_time' in data and data['_time'][0] != "":
                        abs_time = int(data['_time'][0])
                    else:
                        abs_time = None
                    for name, value in data.items():
                        if name != '_time':
                            self.accept(name, abs_time, value, errout)
                    self.accept('sys date', abs_time, [time.strftime("%d/%m/%Y")])
                    self.accept('sys time', abs_time, [time.strftime("%H:%M:%S")])
                except (ValueError, IndexError):
                    print("Invalid packet", line, file=errout)
                    
            # Otherwise print the line
            else:
                print(line, file=txtout)
        
        # Print the last line if it isn't the start of an incomplete packet
        if lines[-1].startswith("@"):
            self.current_line = lines[-1]
        else:
            print(lines[-1], end='', file=txtout)
            self.current_line = ""
        
        # Always update log, even if parse failed
        self.accept('log', abs_time, [text], errout)
        
    def accept(self,
               name: str,
               time: int,
               data: List[str],
               errout: TextIO = sys.stderr) -> bool:
        # Check that name is a valid packet format
        if name not in self.packet_specs:
            print("Received unrecognized data type", name, file=errout)
            return False

        # If a time was recieved, update it and the start time if needed
        if time != None:
            if self.start_time == None:
                self.start_time = time
                time = 0
            else:
                time -= self.start_time

        # Figure out if the spec is a data type or a compund packet spec
        # and generate the list of data types
        spec = self.packet_specs[name]
        if isinstance(spec, DataType):
            data_types = [spec] # type: Sequence[DataType]
        elif isinstance(spec, PacketSpec):
            data_types = spec.data_types
        else:
            raise ValueError("Invalid data spec class")

        if len(data_types) != len(data):
            print("Received invalid number of packet elements for", name, file=errout)

        for data_type, value in zip(data_types, data):
            # Parse each data type and update the stored data
            self.time[data_type.name] = time
            try:
                self.data[data_type.name] = data_type.parse(value)
            except ValueError:
                print("Invalid value for", data_type.name, "recieved:", value, file=errout)
            else:
                # If successful, update the listeners
                for i, (fn, period) in enumerate(self.listeners[data_type.name]):
                    last = self.listener_last_updates[data_type.name][i]
                    if time == None or time - last >= period or time < last:
                        fn(*self.request(data_type.name))
                        if time != None:
                            self.listener_last_updates[data_type.name][i] = time

        return True

    def request(self, name: str) -> Tuple[int, Data]:
        return self.time[name], self.data[name]

DataListener = Callable[[List[int], List[Data]], None]

# Manages the data for a spesific run.  Attatches handlers to a Dispatcher, logs the data when
# running, can save or load data runs in various formats.  Listeners can be attatched that trigger
# on new data when there is an active run
class DataManager:
    def __init__(self, dispatcher: Dispatcher) -> None:
        self.dispatcher = dispatcher
        self.data = OrderedDict((name, ([], [])) for name in dispatcher.data_names) # type: Dict[str, Tuple[List[int], List[Data]]]
        self.last_update_time = 0
        self.listeners = {name: [] for name in dispatcher.data_names} # type: Dict[str, List[DataListener]]
        self.needs_update = {name: False for name in dispatcher.data_names}
        self.running = False

        for name in dispatcher.data_names:
            def fn(time: int, value: Data, name=name):
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
                    self.last_update_time = time
                    self.needs_update[name] = True
            dispatcher.add_listener(name, fn)

    def add_listener(self, name: str, fn: DataListener) -> None:
        self.listeners[name].append(fn)

    def update_listeners(self, name: str) -> None:
        self.needs_update[name] = False
        times, values = self.request(name)
        for listener in self.listeners[name]:
            listener(times, values)

    def update_all_listeners(self, force: bool = False) -> bool:
        updated = False
        for name in self.dispatcher.data_types:
            if self.needs_update[name] or force:
                self.update_listeners(name)
                updated = True
        return updated

    def request(self, name: str) -> Tuple[List[int], List[Data]]:
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

    def dump_csv(self, data_names: Iterable[str], start: int = 0, end: int = None) -> str:
        if end is None:
            end = self.last_update_time
        
        result = "abs time," + ",".join(data_names) + "\n"
        data = {} # type: Dict[int, Dict[str, Data]]
        for name, (times, values) in self.data.items():
            if name in data_names:
                for time, value in zip(times, values):
                    if time >= start and time < end:
                        if time not in data:
                            data[time] = {}
                        data[time][name] = value
        for time, updates in sorted(data.items()):
            result += (str(time) + "," +
                       ",".join(str(updates[n]) if n in updates else ""
                                for n in data_names) + "\n")
        return result

    def dump(self, format: str) -> str:
        if format == 'csv':
            data_names = [name
                          for name in self.dispatcher.data_names
                          if self.dispatcher.data_types[name].one_line]
            return self.dump_csv(data_names)
        elif format == 'json':
            return json.dumps(list(self.data.items()))
        elif format == 'log':
            return "".join(cast(List[str], self.request('log')[1]))
        else:
            sys.exit("Unsupported format " + format)

    # txtout is stream to write non-packet text when loading a log
    def load(self,
             format: str, 
             text: str, txtout:
             TextIO = sys.stdout,
             errout: TextIO = sys.stderr) -> bool:
        if format == 'json':
            data = OrderedDict(json.loads(text))
            if set(self.data.keys()) != set(data.keys()):
                #sys.exit("Invalid fields")
                return False
            else:
                self.data = data
        elif format == 'csv':
            rows = [row.split(',') for row in text.split('\n')]
            for name in rows[0][1:]:
                if name not in self.dispatcher.data_names:
                    return False
            data = OrderedDict([(name, ([], [])) for name in rows[0][1:]])
            for row in rows[1:]:
                for elem, (name, (time_elems, data_elems)) in zip(row[1:], data.items()):
                    if elem != "":
                        elem = self.dispatcher.data_types[name].parse(elem)
                        time_elems.append(int(row[0]))
                        data_elems.append(elem)
            self.data = OrderedDict([(name, data[name] if name in data else ([], []))
                                      for name in self.dispatcher.data_names])
        elif format == 'log':
            self.reset()
            self.start()
            self.dispatcher.acceptText(text, txtout, errout)
            self.stop()
        else:
            sys.exit("Unsupported format" + format)

        last_times = [times[-1] for times, values in self.data.values() if len(times) > 0]
        self.last_update_time = max(last_times) if len(last_times) > 0 else 0
        self.update_all_listeners(True)
        return True
