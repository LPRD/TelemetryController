#!/usr/bin/env python3

from tkinter import *

import manager
import gui
import plot

dts = [#manager.DataType('temperature', float, units='deg C'),
       manager.DataType('x', float, units='Gs'),
       manager.DataType('y', float, units='Gs'),
       manager.DataType('z', float, units='Gs')]
plots = [#plot.Plot('time', 'temperature'),
         plot.Plot('time', ['x', 'y', 'z'], "acceleration vs. time"),
         plot.Plot('y', ['x', 'z'], "vertical vs. horizontal acceleration", 'o')]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root)

if __name__ == '__main__':
    app.mainloop()
