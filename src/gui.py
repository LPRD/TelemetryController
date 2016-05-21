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

import argparse
import math

# Helper class that has a write method that is provided to the constructor
class FnWriteableStream:
    def __init__(self, write):
        self.write = write

# Main gui application class.  Extends frame so an instance can be extended with additional widgets
# directly.  
class Application(Frame):
    def __init__(self, dispatcher, manager, plots, master=None, **flags):
        self.dispatcher = dispatcher
        self.manager = manager
        self.plots = plots
        self.master = master

        # Default values
        new_flags = {'send_with_newline_default': False,
                     'show_current_values': True,
                     'show_send_value': True,
                     'full_screen': False,
                     'backup_log': ".temp_log.json",
                     'serial_console_height': 15}
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
        master.attributes("-fullscreen", self.flags['full_screen'])
        master.bind('<Escape>', self.unmaximize)
        master.wm_title("Telemetry monitor")
        self.createWidgets()
        self.manager.add_listener("sys time", self.saveBackup)

        # Start reading from Serial
        self.serialManager = None
        self.checkSerial()
        ports = serialmanager.serial_ports()
        if args.port:
            if args.port in ports:
                self.serialPort.set(args.port)
            else:
                parser.error("Invalid serial port " + args.port)
        elif ports:
            self.serialPort.set(ports[0])
        if ports:
            self.serialManager = serialmanager.SerialManager(self.dispatcher, self.serialPort.get())
            self.baud.set(self.serialManager.baud)
            self.startSerial()

        self.startListeners()

        # Open a file if requested from command line
        if args.filename:
            extension = args.filename.split(".")[-1]
            if extension not in ["json", "log"]:#, "csv"]:
                parser.error("Invalid file extension \"." + extension + "\"\n" +
                             "Legal formats are json, log")#, csv")
            else:
                self.reset()
                try:
                    if self.manager.load(extension, open(args.filename).read(), self, self.colorStreams['red']):
                        self.valuesList.delete(0, END)
                        self.controlButton.config(text="Reset", bg="grey", command=self.reset)
                    else:
                        parser.error("Invalid data file")
                except FileNotFoundError:
                    parser.error("File " + args.filename + " not found")

    # Initialize the various widgets in the main frame
    def createWidgets(self):
        self.setupPlots()

        buttons = Frame(self)
        self.controlButton = Button(buttons, text="Start", command=self.start, bg="lime green")
        self.controlButton.pack(side=LEFT)

        self.exitButton = Button(buttons, text="Quit", command=self.terminate)
        self.exitButton.pack(side=LEFT)

        self.openButton = Button(buttons, text="Open...", command=self.openFile)
        self.openButton.pack(side=LEFT)

        self.saveButton = Button(buttons, text="Save as...", command=self.saveFile)
        self.saveButton.pack(side=LEFT)
        
        buttons.pack()

        serialLabel = Label(self, text="\nSerial console")
        serialLabel.pack()

        serial = Frame(self)
        serialControls = Frame(serial)

        self.serialPort = StringVar(self)
        self.serialPort.trace('w', self.changeSerial)
        self.serialSelect = OptionMenu(serialControls, self.serialPort, [])
        self.serialSelect.pack(side=LEFT)

        self.baud = StringVar(self)
        self.baud.trace('w', self.changeSerial)
        self.baudSelect = OptionMenu(serialControls, self.baud, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200)
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
        self.namesList = Listbox(valuesTable, width=15, height=len(shown_data_types) + 1)
        self.valuesList = Listbox(valuesTable, width=35, height=len(shown_data_types) + 1)
        self.namesList.insert(0, "abs time (ms)")
        self.valuesList.insert(0, "")
        def fn(xdata, ydata):
            self.valuesList.delete(0)
            self.valuesList.insert(0, str(xdata) if xdata else "")
        self.dispatcher.add_listener('sys time', fn, 100)
        for i, ty in enumerate(shown_data_types):
            if ty.units:
                full_name = ty.name + " (" + ty.units + ")"
            else:
                full_name = ty.name
            self.namesList.insert(i + 1, full_name)
            self.valuesList.insert(i + 1, "")
            def fn(xdata, ydata, i = i):
                self.valuesList.delete(i + 1)
                self.valuesList.insert(i + 1, str(ydata))
            self.dispatcher.add_listener(ty.name, fn, 100)

        self.namesList.pack(side=LEFT)
        self.valuesList.pack()

        if self.flags['show_current_values']:
            valuesTable.pack()

        self.miscGuiPanel = None

    # Set up the plots and add it as a widget
    def setupPlots(self):
        self.fig = matplotlib.figure.Figure(figsize=(10,10),dpi=100)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        width = int(math.ceil(math.sqrt(len(self.plots))))
        height = width - 1 if width * (width - 1) >= len(self.plots) else width
        subplots = {}
        lines = {}
        update = {(plot, y): ([], []) for plot in self.plots for y in plot.ys}
        for i, plot in enumerate(self.plots):
            subplots[plot] = self.fig.add_subplot(width, height, i + 1)
            if plot.name:
                subplots[plot].set_title(plot.name)
            if plot.x == 'time':
                subplots[plot].set_xlabel("time (sec)")
            else:
                subplots[plot].set_xlabel(plot.x +
                                          (" (" + self.dispatcher.data_types[plot.x].units + ")"
                                           if self.dispatcher.data_types[plot.x].units else ""))
            ys_units = [self.dispatcher.data_types[y].units for y in plot.ys]
            assert len(set(ys_units)) <= 1 # All units must be the same, if included
            if ys_units[0]:
                subplots[plot].set_ylabel(ys_units[0])
            for y in plot.ys:
                lines[plot, y], = subplots[plot].plot([], [], label=y)
                
            if len(plot.ys) > 1:
               subplots[plot].legend(loc='lower left') 

            plot.setup_listeners(self.manager, update)

        self.fig.tight_layout(pad=2)

        def animate(i):
            for plot, sp in subplots.items():
                updated = False
                for y in plot.ys:
                    if update[plot, y]:
                        x_data, y_data = update[plot, y]
                        update[plot, y] = None
                        lines[plot, y].set_xdata(x_data)
                        lines[plot, y].set_ydata(y_data)
                        updated = True
                if updated:
                    subplots[plot].relim()
                    subplots[plot].autoscale_view(None, True, True)

        ani = FuncAnimation(self.fig, animate, interval=200)

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.canvas._tkcanvas.pack(side=LEFT)
        #self.update() # Is this needed? Causes freezing with lots of plots

    # Exit, handler for quit button
    def terminate(self):
        if self.manager.running:
            result = askquestion("Exit",
                                 "Logging is running, do you really want to exit?",
                                 icon='warning')
            if result == 'yes':
                sys.exit(0)
        else:  
            sys.exit(0)

    # Write text to the serial console
    def write(self, txt, color=None):
        self.serialOut.config(state=NORMAL)
        if color:
            self.serialOut.insert(END, str(txt), color + '_text')
        else:
            self.serialOut.insert(END, str(txt))
        self.serialOut.see(END)
        self.serialOut.config(state=DISABLED)

    # Start a run
    def start(self):
        if self.serialManager:
            self.manager.start()
            self.controlButton.config(text="Stop", bg="red", command=self.stop)

            for i in range(len(self.dispatcher.data_names)):
                self.valuesList.insert(i, "")
            return True
        else:
            showerror("Error", "No serial port selected")
            return False
    
    # Stop the current run
    def stop(self):
        self.manager.stop()
        self.controlButton.config(text="Reset", bg="grey", command=self.reset)
    
    # Reset for the next run
    def reset(self):
        self.manager.reset()
        self.controlButton.config(text="Start", bg="lime green", command=self.start)
        
    # Send a serial command
    def sendSerial(self, _=None):
        if self.serialManager:
            self.serialManager.write(self.serialIn.get())
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
        
    # Handler for sending a serial command with a newline appended
    def sendSerialNewline(self, _=None):
        if self.serialManager:
            self.serialManager.write(self.serialIn.get() + "\r\n")
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
        
    # Handler for sending a formatted packet
    def sendValues(self, _=None):
        self.sendValue(self.sendDataName.get(), self.sendDataIn.get())
        if self.serialManager:
            self.sendDataIn.delete(0, 'end')

    # Send a formatted packet
    def sendValue(self, name, value=""):
        if self.serialManager:
            self.serialManager.write("@@@@@:" + name + ":" + value + "&&&&&\r\n")
            return True
        else:
            showerror("Error", "No serial port selected")
            return False

    # Disable full-screen mode
    def unmaximize(self, _):
        self.master.attributes("-fullscreen", False)

    # Handler for changing the serial port
    def changeSerial(self, *args):
        #print("Selected port", self.serialPort.get())
        self.serialOut.config(state=NORMAL)
        self.serialOut.delete(1.0, 'end')
        self.serialOut.config(state=DISABLED)
        self.valuesList.delete(0, END)
        self.reset()
        self.serialManager = serialmanager.SerialManager(self.dispatcher, self.serialPort.get())#, int(self.baud.get()))
        self.startSerial()

    # Handler for checking the available serial ports
    def checkSerial(self):
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))

    # Begin updating the data manager listeners
    def startListeners(self):
        if self.manager.update_all_listeners():
            self.after(50, self.startListeners)
        else:
            self.after(100, self.startListeners)

    # Begin reading serial data
    def startSerial(self):
        if self.serialManager:
            try:
                if self.serialManager.handleInput(self, self.colorStreams['red']):
                    self.after(50, self.startSerial)
                else:
                    self.after(100, self.startSerial)
            except OSError:
                self.serialManager = None
                self.checkSerial()

    # Write the current run data log to the backup file
    # TODO: use self.after(...)
    last_update_time = ""
    def saveBackup(self, times, values):
        if len(values) > 0 and values[-1] != self.last_update_time:
            self.last_update_time = values[0]
            open(self.flags["backup_log"], 'w').write(self.manager.dump('json'))

    # Handler to open a file
    def openFile(self):
        filename = askopenfilename()
        if filename:
            extension = filename.split(".")[-1]
            if extension not in ["json", "log"]:#, "csv"]:
                showerror("Error", "Invalid file extension \"." + extension + "\"\n" +
                          "Legal formats are json, log")#, csv")
            else:
                self.reset()
                if self.manager.load(extension, open(filename).read(), self, self.colorStreams['red']):
                    self.valuesList.delete(0, END)
                    self.controlButton.config(text="Reset", bg="grey", command=self.reset)
                else:
                    showerror("Error", "Invalid data file")

    # Handler to save file
    def saveFile(self):
        filename = asksaveasfilename()
        if filename:
            extension = filename.split(".")[-1]
            if extension not in ["json", "csv", "log", # Data formats
                                 "eps", "pdf", "pgf", "png", "ps", "raw", "rgba", "svg", "svgz"]: # Image formats
                showerror("Error", "Invalid file extension \"." + extension + "\"\n"
                          "Legal formats are json, csv, log, eps, pdf, pgf, png, ps, raw, rgba, svg, svgz")
            else:
                if extension in ["json", "csv", "log"]:
                    if self.serialManager:
                        self.serialManager.paused = True
                    open(filename, 'w').write(self.manager.dump(extension))
                    if self.serialManager:
                        self.serialManager.paused = False
                else:
                    self.fig.savefig(filename)

