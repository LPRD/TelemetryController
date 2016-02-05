import serialmanager
import manager

from tkinter import *
from tkinter.scrolledtext import *
#from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror

import matplotlib
#matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

import math

class Application(Frame):
    def __init__(self, manager, master=None):
        self.manager = manager
        self.master = master

        # Init gui
        Frame.__init__(self, master)
        self.pack()
        #master.attributes("-fullscreen", True)
        master.bind('<Escape>', self.unmaximize)
        master.wm_title("Telemetry monitor")
        self.createWidgets()

        # Start reading from Serial
        self.serialManager = None
        self.checkSerial()
        ports = serialmanager.serial_ports()
        if ports:
            self.serialPort.set(ports[0])
            self.serialManager = serialmanager.SerialManager(self.manager, self.serialPort.get())
            self.baud.set(self.serialManager.baud)
            self.startListeners()
            self.startSerial()

        self.startListeners()

    def createWidgets(self):
        self.setupPlots()

        buttons = Frame(self)
        self.controlButton = Button(buttons)
        self.controlButton["text"] = "Start"
        self.controlButton["command"] = self.start
        self.controlButton.pack(side=LEFT)

        self.exitButton = Button(buttons)
        self.exitButton["text"] = "Quit"
        self.exitButton["command"] = self.terminate
        self.exitButton.pack(side=LEFT)

        self.openButton = Button(buttons)
        self.openButton["text"] = "Open..."
        self.openButton["command"] = self.openFile
        self.openButton.pack(side=LEFT)

        self.saveButton = Button(buttons)
        self.saveButton["text"] = "Save as..."
        self.saveButton["command"] = self.saveFile
        self.saveButton.pack(side=LEFT)
        
        buttons.pack()

        serialLabel = Label(self, text="\nSerial console")
        serialLabel.pack()

        serial = Frame(self)
        serialControls = Frame(self)

        self.serialPort = StringVar(self)
        self.serialSelect = OptionMenu(serialControls, self.serialPort, *(serialmanager.serial_ports() + ['<None>']))
        self.serialSelect["text"] = "Select serial port"
        self.serialSelect.pack(side=LEFT)

        self.baud = StringVar(self)
        self.baudSelect = OptionMenu(serialControls, self.baud, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200)
        self.baudSelect["text"] = "Select serial port"
        self.baudSelect.pack(side=LEFT)

        self.selectPortButton = Button(serialControls)
        self.selectPortButton["text"] = "Select"
        self.selectPortButton["command"] = self.changeSerial
        self.selectPortButton.pack()

        serialControls.pack()

        self.serialOut = ScrolledText(serial, width=50, height=20)
        self.serialOut.config(state=DISABLED)
        self.serialOut.pack()

        #serialInLabel = Label(self, text="Serial input")
        #serialInLabel.pack()

        self.serialIn = Entry(serial, width=50)
        self.serialIn.bind('<Return>', self.sendSerial)
        self.serialIn.pack()

        serial.pack()

        valuesLabel = Label(self, text="\nCurrent values")
        valuesLabel.pack()

        valuesTable = Frame(self)
        self.namesList = Listbox(valuesTable, width=15, height=len(self.manager.data_names) + 1)
        self.valuesList = Listbox(valuesTable, width=35, height=len(self.manager.data_names) + 1)
        self.namesList.insert(1, "abs time (ms)")
        def fn(xdata, ydata):
            if xdata:
                self.valuesList.delete(0)
                self.valuesList.insert(0, str(xdata[-1]))
        self.manager.add_listener(self.manager.data_names[0], fn)
        for i, name in enumerate(self.manager.data_names):
            if self.manager.data_types[name].units:
                full_name = name + " (" + self.manager.data_types[name].units + ")"
            else:
                full_name = name
            self.namesList.insert(i + 1, full_name)
            def fn(xdata, ydata, i = i):
                if ydata:
                    self.valuesList.delete(i + 1)
                    self.valuesList.insert(i + 1, str(ydata[-1]))
            self.manager.add_listener(name, fn)

        self.namesList.pack(side=LEFT)
        self.valuesList.pack()
        valuesTable.pack()

    def setupPlots(self):
        self.fig = matplotlib.figure.Figure(figsize=(10,10),dpi=100)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        data_names = [name for name in self.manager.data_names if self.manager.data_types[name].plot]
        width = int(math.ceil(math.sqrt(len(data_names))))
        height = width - 1 if width * (width - 1) >= len(data_names) else width
        subplots = {}
        lines = {}
        for i, name in enumerate(data_names):
            subplots[name] = self.fig.add_subplot(width, height, i + 1)
            subplots[name].set_title(name)
            subplots[name].set_xlabel('time (sec)')
            subplots[name].set_ylabel(self.manager.data_types[name].units if self.manager.data_types[name].units else "")
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

        ani = FuncAnimation(self.fig, animate, interval=100)

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.canvas._tkcanvas.pack(side=LEFT)
        #self.update() # Is this needed? Causes freezing with lots of plots

    def terminate(self):
        sys.exit(0)

    def write(self, txt):
        self.serialOut.config(state=NORMAL)
        self.serialOut.insert(END, str(txt))
        self.serialOut.see(END)
        self.serialOut.config(state=DISABLED)

    def start(self):
        if self.serialManager:
            self.manager.start()
            self.controlButton["text"] = "Stop"
            self.controlButton["command"] = self.stop

            for i in range(len(self.manager.data_names)):
                self.valuesList.insert(i, "")
        else:
            showerror("Error", "No serial port selected")
    
    def stop(self):
        self.manager.stop()
        self.controlButton["text"] = "Reset"
        self.controlButton["command"] = self.reset
    
    def reset(self):
        self.manager.reset()
        self.valuesList.delete(0, END)
        self.controlButton["text"] = "Start"
        self.controlButton["command"] = self.start
        
    def sendSerial(self, _):
        self.serialManager.write(self.serialIn.get())
        self.serialIn.delete(0, 'end')

    def unmaximize(self, _):
        self.master.attributes("-fullscreen", False)

    def changeSerial(self):
        #print("Selected port", self.serialPort.get())
        self.serialManager = serialmanager.SerialManager(self.manager, self.serialPort.get())#, int(self.baud.get()))
        self.startSerial()
        self.reset()

    def checkSerial(self):
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))
        self.after(1000, self.checkSerial)

    def startListeners(self):
        self.manager.update_all_listeners()
        self.after(100, self.startListeners)

    def startSerial(self):
        if self.serialManager:
            self.serialManager.handleInput(self)
            self.after(100, self.startSerial)

    def openFile(self):
        filename = askopenfilename()
        if filename:
            self.reset()
            extension = filename.split('.')[-1]
            self.manager.load(extension, open(filename).read())
            self.valuesList.delete(0, END)
            self.controlButton["text"] = "Reset"
            self.controlButton["command"] = self.reset

    def saveFile(self):
        filename = asksaveasfilename()
        if filename:
            extension = filename.split('.')[-1]
            open(filename, 'w').write(self.manager.dump(extension))
        
