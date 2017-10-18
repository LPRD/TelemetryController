import serialmanager
import manager
import plot

from tkinter import *
from tkinter.scrolledtext import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror, askquestion

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

from collections import OrderedDict
import argparse
import math
import sys
import traceback

from typing import List, Iterable, Callable, Any

class FnWriteableStream:
    """Helper class that has a write method that is provided to the constructor"""
    def __init__(self, write: Callable[[str], None]) -> None:
        self.write = write

class Application(Frame):
    """Main gui application class.  Extends frame so an instance can be extended
    with additional widgets directly.  """
    def __init__(self,
                 dispatcher: manager.Dispatcher,
                 manager: manager.DataManager,
                 plots: Iterable[plot.Plot],
                 master=None,
                 **flags) -> None:
        self.dispatcher = dispatcher
        self.manager = manager
        self.plots = plots
        self.master = master

        # Default values
        new_flags = {'window_manager_title': "Telemetry monitor",
                     'send_with_newline_default': False,
                     'show_current_values': True,
                     'show_send_value': True,
                     'full_screen': False,
                     'backup_log': ".temp_log.json",
                     'serial_console_height': 15,
                     'default_baud': 9600}
        new_flags.update(flags)
        self.flags = new_flags

        # Command-line flags
        parser = argparse.ArgumentParser()
        parser.add_argument('filename',
                            nargs='?',
                            help="default file to open, if provided")
        parser.add_argument('-F','--full-screen',
                            action='store_true',
                            default=self.flags['full_screen'],
                            help="open the gui in full screen mode if requested")
        parser.add_argument('-p','--port',
                            help="default port to open")
        args = parser.parse_args()
        self.flags['full_screen'] = args.full_screen

        # Init gui
        Frame.__init__(self, master)
        self.pack()
        #master.iconbitmap('telemetry.png')
        master.attributes("-fullscreen", self.flags['full_screen'])
        master.bind('<Escape>', self.unmaximize)
        master.wm_title(self.flags['window_manager_title'])
        self._createWidgets()
        self.manager.add_listener("sys time", self.saveBackup)

        # Start reading from Serial
        self.serialManager = None # type: serialmanager.SerialManager
        self.checkSerial()
        self.baud.set(str(self.flags['default_baud']))
        self.serialPort.trace('w', self.changeSerial)
        self.baud.trace('w', self.changeSerial)
        ports = serialmanager.serial_ports()
        if args.port:
            if args.port in ports:
                self.serialPort.set(args.port)
            else:
                parser.error("Invalid serial port " + args.port)
        elif ports:
            self.serialPort.set(ports[0])

        self._startListeners()

        # Open a file if requested from command line
        if args.filename:
            extension = args.filename.split(".")[-1].lower()
            if extension not in ["json", "log", "csv"]:
                parser.error("Invalid file extension \"." + extension + "\"\n" +
                             "Legal formats are json, log, csv")
            else:
                self.reset()
                try:
                    if self.manager.load(extension, open(args.filename).read(), self, self.colorStreams['red']):
                        self.controlButton.config(text="Reset", bg="grey", command=self.reset)
                    else:
                        parser.error("Invalid data file")
                except FileNotFoundError:
                    parser.error("File " + args.filename + " not found")

    def _createWidgets(self):
        """Initialize the various widgets in the main frame."""
        self._setupPlots()

        buttons = Frame(self)
        self.controlButton = Button(buttons, text="Start", command=self.start, bg="lime green")
        self.controlButton.pack(side=LEFT)

        self.exitButton = Button(buttons, text="Quit", command=self.terminate)
        self.exitButton.pack(side=LEFT)

        self.openButton = Button(buttons, text="Open...", command=self.openFile)
        self.openButton.pack(side=LEFT)

        self.saveButton = Button(buttons, text="Save as...", command=self.saveFile)
        self.saveButton.pack(side=LEFT)

        self.exportButton = Button(buttons, text="Export csv...", command=self.exportCSV)
        self.exportButton.pack(side=LEFT)
        
        buttons.pack()

        serialLabel = Label(self, text="\nSerial console")
        serialLabel.pack()

        serial = Frame(self)
        serialControls = Frame(serial)

        self.serialPort = StringVar(self)
        self.serialSelect = OptionMenu(serialControls, self.serialPort, [])
        self.serialSelect.pack(side=LEFT)

        self.baud = StringVar(self)
        self.baudSelect = OptionMenu(serialControls, self.baud, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200, 230400, 250000)
        self.baudSelect.pack(side=LEFT)

        self.refreshPortButton = Button(serialControls, text="Refresh", command=self.checkSerial)
        self.refreshPortButton.pack()

        serialControls.pack()

        self.serialOut = ScrolledText(serial, width=50, height=self.flags['serial_console_height'])
        self.serialOut.config(state=DISABLED)
        self.colorStreams = {}
        for color in ['red', 'yellow', 'green', 'blue']:
            self.serialOut.tag_config(color + '_text', foreground=color)
            self.colorStreams[color] = FnWriteableStream(lambda txt, color=color: self.write(txt, str(color)))
        self.serialOut.pack()

        self.serialIn = Entry(serial, width=50)
        if self.flags["send_with_newline_default"]:
            self.serialIn.bind('<Return>', self.sendSerialNewline)
        else:
            self.serialIn.bind('<Return>', self.sendSerial)
        self.serialIn.pack()

        serialSendButtons = Frame(serial)

        self.sendButton = Button(serialSendButtons, text="Send", command=self.sendSerial)
        self.sendButton.pack(side=LEFT)

        self.sendNewlineButton = Button(serialSendButtons, text="Send with newline", command=self.sendSerialNewline)
        self.sendNewlineButton.pack(side=LEFT)

        serialSendButtons.pack()
        serialSendButtons = Frame(serial)

        serial.pack()

        # Formatted packet sending widget
        sendValuesLabel = Label(self, text="\nSend value")
        if self.flags['show_send_value']:
            sendValuesLabel.pack()

        sendValues = Frame(self)

        self.sendDataName = Entry(sendValues, width=10)
        self.sendDataName.bind('<Return>', self.sendValues)
        self.sendDataName.pack(side=LEFT)

        self.sendDataIn = Entry(sendValues, width=25)
        self.sendDataIn.bind('<Return>', self.sendValues)
        self.sendDataIn.pack(side=LEFT)

        if self.flags['show_send_value']:
            sendValues.pack()

        # Value readout widget
        valuesLabel = Label(self, text="\nCurrent values")
        if self.flags['show_current_values']:
            valuesLabel.pack()

        valuesTable = Frame(self)

        shown_data_types = [self.dispatcher.data_types[name]
                            for name in self.dispatcher.data_names
                            if self.dispatcher.data_types[name].show]
        valuesScrollbar = Scrollbar(valuesTable, orient=VERTICAL)
        self.namesList = Listbox(valuesTable, width=15, height=len(shown_data_types) + 1, yscrollcommand=valuesScrollbar.set)
        self.valuesList = Listbox(valuesTable, width=35, height=len(shown_data_types) + 1, yscrollcommand=valuesScrollbar.set)
        self.namesList.insert(0, "abs time (ms)")
        def fn1(xdata, ydata):
            self.valuesList.delete(0)
            self.valuesList.insert(0, str(xdata) if xdata else "")
        self.dispatcher.add_listener('sys time', fn1, 100)
        for i, ty in enumerate(shown_data_types):
            self.namesList.insert(i + 1, ty.full_name)
            def fn2(xdata: List[float], ydata: List[float], i = i):
                self.valuesList.delete(i + 1)
                self.valuesList.insert(i + 1, str(ydata))
            self.dispatcher.add_listener(ty.name, fn2, 100)

        def yview(*args):
            self.namesList.yview(*args)
            self.valuesList.yview(*args)
        valuesScrollbar.config(command=yview)
        valuesScrollbar.pack(side=RIGHT, fill=Y)

        self.namesList.pack(side=LEFT, fill=BOTH, expand=1)
        self.valuesList.pack(side=LEFT, fill=BOTH, expand=1)

        if self.flags['show_current_values']:
            valuesTable.pack()

        self.miscGuiPanel = None

    def _setupPlots(self):
        """Set up the plots and add it as a widget."""
        self.fig = matplotlib.figure.Figure(figsize=(10,10),dpi=100)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        
        plot.setup(self.plots, self.fig, self.manager)

        def animate(i):
            for plot in self.plots:
                plot.animate()

        ani = FuncAnimation(self.fig, animate, interval=200)

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.canvas._tkcanvas.pack(side=LEFT)
        #self.update() # Is this needed? Causes freezing with lots of plots

    def terminate(self):
        """Exit, handler for quit button."""
        if self.manager.running:
            result = askquestion("Exit",
                                 "Logging is running, do you really want to exit?",
                                 icon='warning')
            if result == 'yes':
                sys.exit(0)
        else:
            sys.exit(0)

    def write(self, txt: str, color: str=None):
        """Write text to the serial console."""
        self.serialOut.config(state=NORMAL)
        if color:
            self.serialOut.insert(END, str(txt), color + '_text')
        else:
            self.serialOut.insert(END, str(txt))
        self.serialOut.see(END)
        self.serialOut.config(state=DISABLED)

    def start(self):
        """Start a run."""
        if self.serialManager:
            self.resetValuesList()
            self.manager.start()
            self.controlButton.config(text="Stop", bg="red", command=self.stop)
            return True
        else:
            showerror("Error", "No serial port selected")
            return False
    
    def stop(self):
        """Stop the current run."""
        self.manager.stop()
        self.controlButton.config(text="Reset", bg="grey", command=self.reset)
    
    def reset(self):
        """Reset for the next run."""
        self.resetValuesList()
        self.manager.reset()
        self.controlButton.config(text="Start", bg="lime green", command=self.start)
    
    def sendSerial(self, _=None):
        """Send a serial command."""
        if self.serialManager:
            self.serialManager.write(self.serialIn.get())
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
    
    def sendSerialNewline(self, _=None):
        """Handler for sending a serial command with a newline appended."""
        if self.serialManager:
            self.serialManager.write(self.serialIn.get() + "\r\n")
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
    
    def sendValues(self, _=None):
        """Handler for sending a formatted packet."""
        self.sendValue(self.sendDataName.get(), self.sendDataIn.get())
        if self.serialManager:
            self.sendDataIn.delete(0, 'end')
    
    def sendValue(self, name, value=""):
        """Send a formatted packet."""
        if self.serialManager:
            self.serialManager.write("@@@@@" + name + ":" + manager.unparse(value) + "&&&&&\r\n")
            return True
        else:
            showerror("Error", "No serial port selected")
            return False
    
    def unmaximize(self, _):
        """Disable full-screen mode."""
        self.master.attributes("-fullscreen", False)
    
    def resetValuesList(self):
        """Clear the values list after a reset or changing ports."""
        shown_data_types = [self.dispatcher.data_types[name]
                            for name in self.dispatcher.data_names
                            if self.dispatcher.data_types[name].show]
        self.valuesList.delete(0, END)
        for i in range(len(shown_data_types) + 1):
            self.valuesList.insert(i, "")
    
    def changeSerial(self, *args):
        """Handler for changing the serial port."""
        # Try-catch needed b/c error messages in tracebacks on Windows are buggy
        try:
            #print("Selected port", self.serialPort.get())
            self.serialOut.config(state=NORMAL)
            self.serialOut.delete(1.0, 'end')
            self.serialOut.config(state=DISABLED)
            self.reset()
            self.serialManager = serialmanager.SerialManager(self.dispatcher, self.serialPort.get(), int(self.baud.get()))
            self.startSerial()
        except:
            if not sys.platform.startswith('win'):
                traceback.print_exc()
    
    def checkSerial(self):
        """Handler for checking the available serial ports."""
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))
    
    def _startListeners(self):
        """Begin updating the data manager listeners."""
        if self.manager.update_all_listeners():
            self.after(50, self._startListeners)
        else:
            self.after(100, self._startListeners)
    
    def startSerial(self):
        """Begin reading serial data."""
        if self.serialManager:
            try:
                if self.serialManager.handleInput(self, self.colorStreams['red']):
                    self.after(50, self.startSerial)
                else:
                    self.after(100, self.startSerial)
            except OSError:
                self.serialManager = None
                self.checkSerial()
    
    _last_update_time = ""
    def saveBackup(self, times, values):
        """Write the current run data log to the backup file once per second
        while collecting data."""
        # TODO: use self.after(...)
        if len(values) > 0 and values[-1] != self._last_update_time:
            self._last_update_time = values[0]
            open(self.flags["backup_log"], 'w').write(self.manager.dump('json'))
    
    def openFile(self):
        """Handler to open a file."""
        filename = askopenfilename(filetypes=[('All files', '*.*'), 
                                              ('JSON data file', '*.json'),
                                              ('Log file', '*.log'),
                                              ('Comma-seperated values', '*.csv')])
        if filename:
            extension = filename.split(".")[-1].lower() if "." in filename else ""
            if extension not in ["json", "log", "csv"]:
                if extension:
                    showerror("Error", "Invalid file extension \"" + extension + "\"\n" +
                              "Legal formats are json, log, csv")
                else:
                    showerror("Error", "Missing file extension\n" +
                              "Legal formats are json, log, csv")
            else:
                self.reset()
                if self.manager.load(extension, open(filename).read(), self, self.colorStreams['red']):
                    self.controlButton.config(text="Reset", bg="grey", command=self.reset)
                else:
                    showerror("Error", "Invalid data file")
    
    def saveFile(self):
        """Handler to save to a file."""
        filename = asksaveasfilename(defaultextension='.json',
                                     filetypes=[('JSON data file (recommended)', '*.json'),
                                                ('Log file', '*.log'),
                                                ('Comma-seperated values', '*.csv'),
                                                ('EPS-embedded image', '*.eps'),
                                                ('PDF-embedded image', '*.pdf'),
                                                ('PFG-embedded image', '*.pfg'),
                                                ('PNG image', '*.png'),
                                                ('PostScript-embedded image', '*.ps'),
                                                ('RAW image', '*.raw'),
                                                ('RBGA image', '*.rbga'),
                                                ('SVG image', '*.svg'),
                                                ('SVGZ image', '*.svgz')])
        if filename:
            extension = filename.split(".")[-1] if "." in filename else ""
            if extension not in ["json", "log", "csv", # Data formats
                                 "eps", "pdf", "pgf", "png", "ps", "raw", "rgba", "svg", "svgz"]: # Image formats
                if extension:
                    showerror("Error", "Invalid file extension \"" + extension + "\"\n"
                              "Legal formats are json, csv, log, eps, pdf, pgf, png, ps, raw, rgba, svg, svgz")
                else:
                    showerror("Error", "Missing file extension\n" +
                              "Legal formats are json, csv, log, eps, pdf, pgf, png, ps, raw, rgba, svg, svgz")
            else:
                if extension in ["json", "log", "csv"]:
                    if self.serialManager:
                        self.serialManager.paused = True
                    open(filename, 'w').write(self.manager.dump(extension))
                    if self.serialManager:
                        self.serialManager.paused = False
                else:
                    self.fig.savefig(filename)
    
    def exportCSV(self):
        """Handler to export as a CSV file."""
        filename = asksaveasfilename()
        if filename:
            if filename.split(".")[-1] != "csv":
                showerror("Error", "Invalid file extension\n" +
                          "Filename must end in .csv")
            
            # Create a popup window to ask for settings of what data to include
            exportWindow = Toplevel(self)
            exportWindow.title("Export settings")
            
            startTimeLabel = Label(exportWindow, text="Start time (sec)")
            startTimeLabel.grid(row=0, column=0)

            startTimeVar = DoubleVar()
            startTimeVar.set(0)

            startTimeEntry = None
            
            lastValidStartTime = 0
            def validateStartTime(value):
                nonlocal lastValidStartTime
                if value == '':
                    return True
                try:
                    lastValidStartTime = float(value)
                    if lastValidStartTime < 0:
                        lastValidStartTime = 0
                        return False
                    else:
                        return True
                except ValueError:
                    return False

            startTimeEntry = Entry(exportWindow,
                                   textvariable=startTimeVar,
                                   validate='all',
                                   validatecommand=(exportWindow.register(validateStartTime), '%P'),
                                   width=10)
            startTimeEntry.grid(row=0, column=1)

            endTimeLabel = Label(exportWindow, text="End time (sec)")
            endTimeLabel.grid(row=1, column=0)
            
            lastUpdateTime = self.manager.last_update_time / 1000

            endTimeVar = DoubleVar()
            endTimeVar.set(lastUpdateTime)

            endTimeEntry = None
            
            lastValidEndTime = lastUpdateTime
            def validateEndTime(value):
                nonlocal lastValidEndTime
                if value == '':
                    return True
                try:
                    lastValidEndTime = float(value)
                    if lastValidEndTime < 0:
                        lastValidEndTime = 0
                        return False
                    else:
                        return True
                except ValueError:
                    return False
            
            endTimeEntry = Entry(exportWindow,
                                 textvariable=endTimeVar,
                                 validate='all',
                                 validatecommand=(exportWindow.register(validateEndTime), '%P'),
                                 width=10)
            endTimeEntry.grid(row=1, column=1)
            
            names = OrderedDict()
            data_types = list(filter(lambda data: data.one_line,
                                     self.dispatcher.data_types.values()))
            num_data_rows = math.ceil(len(list(data_types)) / 2)
            for i, data in enumerate(data_types):
                var = IntVar()
                var.set(data.export_csv)
                cb = Checkbutton(exportWindow, text=data.name, variable=var)
                cb.grid(row=i % num_data_rows + 2, column=i // num_data_rows, sticky=W)
                names[data.name] = var

            ok = False
            def accept():
                nonlocal ok
                ok = True
                exportWindow.destroy()

            exportButton = Button(exportWindow, text='Export', command=accept)
            exportButton.grid(row=num_data_rows + 2, column=0, sticky=E)
            cancelButton = Button(exportWindow, text='Cancel', command=exportWindow.destroy)
            cancelButton.grid(row=num_data_rows + 2, column=1, sticky=W)

            self.wait_window(exportWindow)
            
            if ok:
                selected_data = [name for name, var in names.items() if var.get()]
                start_time = lastValidStartTime * 1000
                end_time = lastValidEndTime * 1000
                for data, (name, var) in zip(self.dispatcher.data_types.values(), names.items()):
                    data.export_csv = bool(var.get())
                open(filename, 'w').write(self.manager.dump_csv(selected_data, start_time, end_time))
