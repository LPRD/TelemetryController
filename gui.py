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
        self.checkPorts()
        ports = serialmanager.serial_ports()
        if ports:
            self.serialPort.set(ports[0])
            self.serialManager = serialmanager.SerialManager(self.manager, self.serialPort.get())
            self.startListeners()
            self.startSerial()
        else:
            self.serialManager = None

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

        serialControlLabel = Label(self, text="Serial port")
        serialControlLabel.pack()

        serialControl = Frame(self)

        self.serialPort = StringVar(self)
        self.serialSelect = OptionMenu(serialControl, self.serialPort, *(serialmanager.serial_ports() + ['<None>']))
        self.serialSelect["text"] = "Select serial port"
        self.serialSelect.pack(side=LEFT)

        self.selectPortButton = Button(serialControl)
        self.selectPortButton["text"] = "Select"
        self.selectPortButton["command"] = self.changePort
        self.selectPortButton.pack()

        serialControl.pack()

        serialLabel = Label(self, text="Serial console")
        serialLabel.pack()

        self.serial = ScrolledText(self, width=50)
        self.serial.config(state=DISABLED)
        self.serial.pack()

        serialInLabel = Label(self, text="Serial input")
        serialInLabel.pack()

        self.serialIn = Entry(self)
        self.serialIn.bind('<Return>', self.sendSerial)
        self.serialIn.pack()

        valuesLabel = Label(self, text="Current values")
        valuesLabel.pack()

        valuesTable = Frame(self)
        self.namesList = Listbox(valuesTable, width=10)
        self.valuesList = Listbox(valuesTable, width=30)
        self.namesList.insert(1, "time (ms)")
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
        if self.serialManager and self.serialManager.running:
            self.serialManager.stop()
        sys.exit(0)

    def write(self, txt):
        self.serial.config(state=NORMAL)
        self.serial.insert(END, str(txt))
        self.serial.see(END)
        self.serial.config(state=DISABLED)

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
        self.serial.config(state=NORMAL)
        self.serial.delete(1.0, 'end')
        self.serial.config(state=DISABLED)
        self.valuesList.delete(0, END)
        self.controlButton["text"] = "Start"
        self.controlButton["command"] = self.start
        
    def sendSerial(self, _):
        self.serialManager.write(self.serialIn.get())
        self.serialIn.delete(0, 'end')

    def unmaximize(self, _):
        self.master.attributes("-fullscreen", False)

    def changePort(self):
        #print("Selected port", self.serialPort.get())
        if self.serialManager and self.serialManager.running:
            self.serialManager.stop()
        self.serialManager = serialmanager.SerialManager(self.manager, self.serialPort.get())
        self.startSerial()
        self.reset()

    def checkPorts(self):
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))
        self.after(1000, self.checkPorts)

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
        
