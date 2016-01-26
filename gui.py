import serialmanager
import manager

from tkinter import *
from tkinter.scrolledtext import *

import matplotlib
#matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

import math

class Application(Frame):
    def __init__(self, manager, master=None):
        self.master = master

        self.manager = manager

        # Init gui
        Frame.__init__(self, master)
        self.pack()
        master.attributes("-fullscreen", True)
        master.bind('<Escape>', self.unmaximize)
        self.createWidgets()

        # Start reading from Serial
        self.checkPorts()
        self.serialPort.set(serialmanager.serial_ports()[0])
        self.serialReader = serialmanager.SerialManager(self.manager, self.serialPort.get())
        self.startSerial()

    def createWidgets(self):
        self.fig = matplotlib.figure.Figure(figsize=(10,10),dpi=100)
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(self.fig, master=self)
        data_names = [name for name in self.manager.data_names if self.manager.data_types[name].plot]
        dim = int(math.ceil(math.sqrt(len(data_names))))
        subplots = {}
        for i, name in enumerate(data_names):
            subplots[name] = self.fig.add_subplot(dim, dim, i + 1)
        self.fig.tight_layout()

        def animate(i):
            for name, sp in subplots.items():
                x_data, y_data = self.manager.request(name)
                sp.clear()
                sp.set_xlabel('time (sec)')
                sp.set_ylabel(name)
                sp.plot([x / 1000 for x in x_data], y_data)

        ani = FuncAnimation(self.fig, animate, interval=100)

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=LEFT)
        self.canvas._tkcanvas.pack(side=LEFT)
        self.update()

        buttons = Frame(self)
        self.controlButton = Button(buttons)
        self.controlButton["text"] = "Start"
        self.controlButton["command"] = self.start
        self.controlButton.pack(side=LEFT)

        self.exitButton = Button(buttons)
        self.exitButton["text"] = "Quit"
        self.exitButton["command"] = sys.exit
        self.exitButton.pack(side=LEFT)

        self.serialPort = StringVar(self)
        self.serialSelect = OptionMenu(buttons, self.serialPort, *serialmanager.serial_ports(), command=self.changePort)
        self.serialSelect["text"] = "Select serial port"
        self.serialSelect.pack()
        
        buttons.pack()

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

    def write(self, txt):
        self.serial.config(state=NORMAL)
        self.serial.insert(END, str(txt))
        self.serial.see(END)
        self.serial.config(state=DISABLED)

    def start(self):
        self.manager.start()
        self.controlButton["text"] = "Reset"
        self.controlButton["command"] = self.reset
    
    def reset(self):
        self.manager.reset()
        self.serial.config(state=NORMAL)
        self.serial.delete(1.0, 'end')
        self.serial.config(state=DISABLED)
        self.controlButton["text"] = "Start"
        self.controlButton["command"] = self.start

    def startSerial(self):
        self.serialReader.tryInput(self)
        self.after(10, self.startSerial)
        
    def sendSerial(self, _):
        self.serialReader.write(self.serialIn.get())
        self.serialIn.delete(0, 'end')

    def unmaximize(self, _):
        self.master.attributes("-fullscreen", False)

    def changePort(self, _):
        self.serialReader = serialmanager.SerialManager(self.manager, self.serialPort.get())

    def checkPorts(self):
        self.serialSelect['menu'].delete(0, 'end')
        for port in serialmanager.serial_ports():
            self.serialSelect['menu'].add_command(label=port, command=lambda p=port: self.serialPort.set(p))
        self.after(1000, self.checkPorts)

        
