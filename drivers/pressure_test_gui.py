#!/usr/bin/env python3

import sys
sys.path.append("src")

from tkinter import *

import manager
import gui
import plot

dts = [manager.DataType('pressure', float, units='psi'),
       manager.DataType('angle', int, units='degrees')]
plots = [plot.Plot('time', 'pressure'),
         plot.Plot('time', 'angle')]
         #plot.Plot('pressure', 'angle')]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      serial_console_height=10,
                      default_baud=9600)

if __name__ == '__main__':
    app.mainloop()
