import serialmanager
import manager

from tkinter import *
from tkinter.scrolledtext import *
#from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror, askquestion

import matplotlib
#matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

import math

class Application(Frame):
    def __init__(self, dispatcher, manager, master=None, **flags):
        self.dispatcher = dispatcher
        self.manager = manager
        self.master = master

        # Defaults
        new_flags = {'send_with_newline_default': False,
                     'show_current_values': True,
                     'show_send_value': True,
                     'full_screen': False,
                     'backup_log': ".temp_log.json",
                     'serial_console_height': 15}
        new_flags.update(flags)
        self.flags = new_flags

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
        if ports:
            self.serialPort.set(ports[0])
            self.serialManager = serialmanager.SerialManager(self.dispatcher, self.serialPort.get())
            self.baud.set(self.serialManager.baud)
            self.startSerial()

        self.startListeners()

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

    def setupPlots(self):
        self.fig = matplotlib.figure.Figure(figsize=(10,10),dpi=100)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        data_names = [name for name in self.dispatcher.data_names if self.dispatcher.data_types[name].plot]
        width = int(math.ceil(math.sqrt(len(data_names))))
        height = width - 1 if width * (width - 1) >= len(data_names) else width
        subplots = {}
        lines = {}
        for i, name in enumerate(data_names):
            subplots[name] = self.fig.add_subplot(width, height, i + 1)
            subplots[name].set_title(name)
            subplots[name].set_xlabel('time (sec)')
            subplots[name].set_ylabel(self.dispatcher.data_types[name].units if self.dispatcher.data_types[name].units else "")
            lines[name], = subplots[name].plot([], [])
        self.fig.tight_layout(pad=2)

        update = {name: ([], []) for name in data_names}

        max_points = 1000

        def get_listener(name):
            def fn(x_data, y_data):
                assert len(x_data) == len(y_data)
                # 'Prune' plotted data to avoid slow-down
                indices = range(0, len(x_data), max(len(x_data) // max_points, 1))
                x_data = [x_data[i] for i in indices]
                y_data = [y_data[i] for i in indices]
                update[name] = x_data, y_data
            return fn

        for name in data_names:
            self.manager.add_listener(name, get_listener(name))

        def animate(i):
            for name, sp in subplots.items():
                if update[name]:
                    x_data, y_data = update[name]
                    update[name] = None
                    lines[name].set_xdata([x / 1000 for x in x_data])
                    lines[name].set_ydata(y_data)
                    subplots[name].relim()
                    subplots[name].autoscale_view(None, True, True)

        ani = FuncAnimation(self.fig, animate, interval=200)

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.canvas._tkcanvas.pack(side=LEFT)
        #self.update() # Is this needed? Causes freezing with lots of plots

    def terminate(self):
        if self.manager.running:
            result = askquestion("Exit",
                                 "Logging is running, do you really want to exit?",
                                 icon='warning')
            if result == 'yes':
                sys.exit(0)
        else:  
            sys.exit(0)

    def write(self, txt):
        self.serialOut.config(state=NORMAL)
        self.serialOut.insert(END, str(txt))
        self.serialOut.see(END)
        self.serialOut.config(state=DISABLED)

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
    
    def stop(self):
        self.manager.stop()
        self.controlButton.config(text="Reset", bg="grey", command=self.reset)
    
    def reset(self):
        self.manager.reset()
        self.controlButton.config(text="Start", bg="lime green", command=self.start)
        
    def sendSerial(self, _=None):
        if self.serialManager:
            self.serialManager.write(self.serialIn.get())
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
        
    def sendSerialNewline(self, _=None):
        if self.serialManager:
            self.serialManager.write(self.serialIn.get() + "\r\n")
            self.serialIn.delete(0, 'end')
        else:
            showerror("Error", "No serial port selected")
        
    def sendValues(self, _=None):
        self.sendValue(self.sendDataName.get(), self.sendDataIn.get())
        if self.serialManager:
            self.sendDataIn.delete(0, 'end')

    def sendValue(self, name, value=""):
        if self.serialManager:
            self.serialManager.write("@@@@@:" + name + ":" + value + "&&&&&\r\n")
            return True
        else:
            showerror("Error", "No serial port selected")
            return False


    def unmaximize(self, _):
        self.master.attributes("-fullscreen", False)

    def changeSerial(self, *args):
        #print("Selected port", self.serialPort.get())
        self.serialOut.config(state=NORMAL)
        self.serialOut.delete(1.0, 'end')
        self.serialOut.config(state=DISABLED)
        self.valuesList.delete(0, END)
        self.reset()
        self.serialManager = serialmanager.SerialManager(self.dispatcher, self.serialPort.get())#, int(self.baud.get()))
        self.startSerial()

    def checkSerial(self):
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))

    def startListeners(self):
        if self.manager.update_all_listeners():
            self.after(50, self.startListeners)
        else:
            self.after(100, self.startListeners)

    def startSerial(self):
        if self.serialManager:
            try:
                if self.serialManager.handleInput(self):
                    self.after(50, self.startSerial)
                else:
                    self.after(100, self.startSerial)
            except OSError:
                self.serialManager = None
                self.checkSerial()

    last_update_time = ""
    def saveBackup(self, times, values):
        if len(values) > 0 and values[-1] != self.last_update_time:
            self.last_update_time = values[0]
            open(self.flags["backup_log"], 'w').write(self.manager.dump('json'))

    def openFile(self):
        filename = askopenfilename()
        if filename:
            extension = filename.split(".")[-1]
            if extension not in ["json", "log"]:#, "csv"]:
                showerror("Error", "Invalid file extension \"." + extension + "\"\n" +
                          "Legal formats are json, log")#, csv")
            else:
                self.reset()
                if self.manager.load(extension, open(filename).read(), self):
                    self.valuesList.delete(0, END)
                    self.controlButton.config(text="Reset", bg="grey", command=self.reset)
                else:
                    showerror("Error", "Invalid data file")

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
                    self.serialManager.paused = True
                    open(filename, 'w').write(self.manager.dump(extension))
                    self.serialManager.paused = False
                else:
                    self.fig.savefig(filename)

