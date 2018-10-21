
from collections import OrderedDict
import itertools
import copy
import time
import json
import sys

from typing import cast, Any, Union, List, Tuple, NamedTuple, Dict, Callable, Iterable, Sequence
from typing.io import TextIO

# Data handling functions
def parse(type: type, value: str):
    """Parse a string to get a value of a given type."""
    # bool doesn't actually parse the value, just checks whether string is empty
    if type is bool:
        return value == "1" or value == "True"
    else:
        return type(value)

def unparse(value) -> str:
    """Convert a value to a string that we can send."""
    # Treat bools as ints
    if type(value) is bool:
        value = int(value)
    return str(value)

Data = Union[bool, int, float, str]

class DataType:
    """Representation of a data value category, with various properties."""
    def __init__(self,
                 name:       str,
                 type:       type = float,
                 show:       bool = True,
                 one_line:   bool = True,
                 export_csv: bool = False,
                 thresholds: Tuple[Data, Data] = None,
                 units:      str  = None) -> None:
        self.name = name
        self.type = type
        # bool doesn't actually parse the value, just checks whether string is empty
        self.parse = lambda value: parse(type, value)
        self.show = show
        self.one_line = one_line
        self.export_csv = export_csv
        if thresholds and thresholds[1] < thresholds[0]:
            raise ValueError("lower must be less than upper")
        self.thresholds = thresholds
        self.units = units

        self.full_name = self.name.replace("_", " ")
        if self.units:
            self.full_name += " (" + self.units + ")"

class PacketSpec:
    """Representation of a serial packet that contains multiple data types."""
    def __init__(self, name: str, *data_types: DataType) -> None:
        self.name = name
        self.data_types = data_types

Spec = Union[PacketSpec, DataType]
DispatchListener = Callable[[int, Data], None]

class Dispatcher:
    """Manages parsing incoming serial packets, recieving data in given data
    types, and passes it to listeners.  Also tracks system date and time.  """
    
    start_time = None # type: int
    _current_line = ""
    
    def __init__(self, *specs: Spec) -> None:
        specs = (DataType('sys date', str),
                 DataType('sys time', str),
                 DataType('log', str, False, False)) + specs
        data_types = tuple(s for s in specs if isinstance(s, DataType))

        self.packet_specs = OrderedDict((s.name, s) for s in specs)
        self.data_names = [d.name for d in data_types]
        self.data_types = OrderedDict((d.name, d) for d in data_types)
        self.data = {name: None for name in self.data_names} # type: Dict[str, Data]
        self.time = {name: None for name in self.data_names} # type: Dict[str, int]
        self.listeners = {name: [] for name in self.data_names} # type: Dict[str, List[Tuple[DispatchListener, int]]]
        self.listener_last_updates = {name: [] for name in self.data_names} # type: Dict[str, List[int]]

    def reset(self):
        """Reset the states of all listeners as if no data had been received."""
        self.start_time = None
        for name in self.data_names:
            for i in range(len(self.listener_last_updates[name])):
                self.listener_last_updates[name][i] = 0

    def add_listener(self, name: str, fn: DispatchListener, period=0):
        """Attatch a new listener function to a data field, with an optional
        delay between updates."""
        self.listeners[name].append((fn, period))
        self.listener_last_updates[name].append(0)

    def acceptText(self,
                   text: str,
                   txtout: TextIO = sys.stdout,
                   errout: TextIO = sys.stderr):
        """Eat a raw string of data, parse it, and dispatch the new values
        appropriately."""
        # Split the unparsed text from previously with the new text into lines
        lines = (self._current_line + text).split("\n")

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
            self._current_line = lines[-1]
        else:
            print(lines[-1], end='', file=txtout)
            self._current_line = ""
        
        # Always update log, even if parse failed
        self.accept('log', abs_time, [text], errout)
        
    def accept(self,
               name: str,
               time: int,
               data: List[str],
               errout: TextIO = sys.stderr) -> bool:
        """Accept a new value for a field, and dispatch it appropriately."""
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
        """Get the current value of any data field and the time that it was
        recieved, by name"""
        return self.time[name], self.data[name]

DataListener = Callable[[List[int], List[Data]], None]

class DataManager:
    """Manages the data for a spesific run.  Attatches handlers to a Dispatcher,
    logs the data when running, can save or load data runs in various formats.  
    Listeners can be attatched that trigger on new data when there is an active
    run."""

    running = False
    
    def __init__(self, dispatcher: Dispatcher) -> None:
        self.dispatcher = dispatcher
        self.data = OrderedDict((name, ([], [])) for name in dispatcher.data_names) # type: Dict[str, Tuple[List[int], List[Data]]]
        self.thresholds = OrderedDict((name, data.thresholds)
                                      for name, data in dispatcher.data_types.items()
                                      if data.thresholds) # type: Dict[str, Tuple[Data, Data]]
        self.threshold_data = OrderedDict((name, ([], [])) for name in dispatcher.data_names) # type: Dict[str, Tuple[List[int], List[Data]]]
        self.last_update_time = 0
        self.listeners = {name: [] for name in dispatcher.data_names} # type: Dict[str, List[DataListener]]
        self.needs_update = {name: False for name in dispatcher.data_names}

        for name in dispatcher.data_names:
            def fn(time: int, value: Data, name=name):
                if self.running and time != None:
                    # If the time jumps backward (recieved a corrupted timestamp)
                    # overwrite the most recent data point
                    if (len(self.data[name][0]) > 0 and
                        (time < self.data[name][0][-1] or self.data[name][0][-1] < 0)):
                        self.data[name][0][-1] = time
                        self.data[name][1][-1] = value
                        if self.is_valid(name, value):
                            self.threshold_data[name][0][-1] = time
                            self.threshold_data[name][1][-1] = value
                    else:
                        self.data[name][0].append(time)
                        self.data[name][1].append(value)
                        if self.is_valid(name, value):
                            self.threshold_data[name][0].append(time)
                            self.threshold_data[name][1].append(value)
                    self.last_update_time = time
                    self.needs_update[name] = True
            dispatcher.add_listener(name, fn)

    def add_listener(self, name: str, fn: DataListener) -> None:
        """Attatch a new listener function to a data field."""
        self.listeners[name].append(fn)

    def update_listeners(self, name: str) -> None:
        """Perform an update of all listeners attatched to the given field."""
        self.needs_update[name] = False
        times, values = self.request(name)
        for listener in self.listeners[name]:
            listener(times, values)

    def update_all_listeners(self, force: bool = False) -> bool:
        """Perform an update of all listeners, optionally forcing an update
        regardless of whether new data was present."""
        updated = False
        for name in self.dispatcher.data_types:
            if self.needs_update[name] or force:
                self.update_listeners(name)
                updated = True
        return updated

    def is_valid(self, name: str, value: Data) -> bool:
        """Test if a value is valid for the current thresholds."""
        if name in self.thresholds:
            return self.thresholds[name][0] < value < self.thresholds[name][1]
        else:
            return True

    def get_default_threshold(self, name: str):
        """Get the current lower and upper values of threshold data."""
        if name in self.thresholds:
            return self.thresholds[name]
        else:
            return min(self.data[name][1]), max(self.data[name][1])
    
    def set_threshold(self, name: str, lower: Data, upper: Data):
        """Set a lower and upper threshold for data to consider."""
        if not hasattr(self.dispatcher.data_types[name].type, '__lt__'):
            raise ValueError("Cannot set threshold for " + name)
        if upper < lower:
            raise ValueError("Invalid threshold for {}: lower must be less than upper"
                             .format(name))
        self.thresholds[name] = lower, upper
        self.threshold_data[name] = ([], [])
        for time, value in zip(*self.data[name]):
            if lower <= value <= upper:
                self.threshold_data[name][0].append(time)
                self.threshold_data[name][1].append(value)
        self.update_all_listeners(True)

    def reset_thresholds(self):
        """Remove all set thresholds."""
        self.thresholds.clear()
        self.threshold_data = copy.deepcopy(self.data)
        self.update_all_listeners(True)

    def request(self, name: str) -> Tuple[List[int], List[Data]]:
        """Request all run data for a field."""
        return self.threshold_data[name]

    def start(self):
        """Begin taking data and updating the listeners."""
        self.dispatcher.reset()
        self.running = True
        self.update_all_listeners(True)

    def stop(self):
        """Halt taking data and updating the listeners."""
        self.running = False
        self.update_all_listeners(True)

    def reset(self):
        """Reset the most recent stored run data."""
        for times, values in itertools.chain(self.data.values(), self.threshold_data.values()):
            times.clear()
            values.clear()
        self.running = False
        self.update_all_listeners(True)

    def dump_csv(self, data_names: Iterable[str], start: int = 0, end: int = None) -> str:
        """Dump the current run data for the given data fields at the given
        indices to a csv data string."""
        if end is None:
            end = self.last_update_time
        
        result = "abs time," + ",".join(data_names) + "\n"
        data = {} # type: Dict[int, Dict[str, Data]]
        for name, (times, values) in self.threshold_data.items():
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
        """Dump the current run data to a string representation in one of the
        following formats:
        * csv: A csv log containing all data from most fields.
        * json: A json representation of the entire internal state of the current
        run, that may be reloaded for analysis.
        * log: All recieved data appended into a single string."""
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

  
    def load(self,
             format: str, 
             text: str,
             # streams to write non-packet output when loading a log
             txtout: TextIO = sys.stdout,
             errout: TextIO = sys.stderr):
        """Load a string representation of run data from one of the following
        formats, as generated by dump():
        * csv: A csv log containing all data from most fields.
        * json: A json representation of the entire internal state of the current
        run, that may be reloaded for analysis.
        * log: All recieved data appended into a single string."""
        if format == 'json':
            data = OrderedDict(json.loads(text))
            if set(self.data.keys()) != set(data.keys()):
                raise ValueError("Unexpected data fields: expected {}, found {}"
                                 .format(str(sorted(self.data.keys())), str(sorted(data.keys()))))
            else:
                self.data = data
                for name, (times, values) in data.items():
                    for time, value in zip(times, values):
                        if self.is_valid(name, value):
                            self.threshold_data[name][0].append(time)
                            self.threshold_data[name][1].append(value)
        
        elif format == 'csv':
            rows = [row.split(',') for row in text.split('\n')]
            for name in rows[0][1:]:
                if name not in self.dispatcher.data_names:
                    raise ValueError("Unexpected data field: " + name)
            data = OrderedDict([(name, ([], [])) for name in rows[0][1:]])
            for row in rows[1:]:
                for elem, (name, (time_elems, data_elems)) in zip(row[1:], data.items()):
                    if elem != "":
                        elem = self.dispatcher.data_types[name].parse(elem)
                        time_elems.append(int(row[0]))
                        data_elems.append(elem)
            self.data = OrderedDict([(name, data[name] if name in data else ([], []))
                                      for name in self.dispatcher.data_names])
            for name, (times, values) in self.data.items():
                for time, value in zip(times, values):
                    if self.is_valid(name, value):
                        self.threshold_data[name][0].append(time)
                        self.threshold_data[name][1].append(value)
        
        elif format == 'log':
            self.reset()
            self.start()
            self.dispatcher.acceptText(text, txtout, errout)
            self.stop()
        else:
            raise ValueError("Unsupported format" + format)

        last_times = [times[-1] for times, values in self.data.values() if len(times) > 0]
        self.last_update_time = max(last_times) if len(last_times) > 0 else 0
        self.update_all_listeners(True)
        
