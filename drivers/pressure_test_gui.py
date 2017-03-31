#!/usr/bin/env python3

import sys
sys.path.append("src")

from tkinter import *

import manager
import gui
import plot

dts = [manager.DataType('pressure_in', float, units='psi', export_csv=True),
       manager.DataType('pressure_out', float, units='psi', export_csv=True),
       manager.DataType('pressure_drop', float, units='psi', export_csv=True),
       manager.DataType('fuel_angle', int, units='degrees', export_csv=True),
       manager.DataType('oxygen_angle', int, units='degrees', export_csv=True)]
plots = [plot.Plot('time', ['pressure_in', 'pressure_out', 'pressure_drop']),
         plot.Plot('time', ['fuel_angle', 'oxygen_angle'])]
         #plot.Plot('pressure', 'angle')]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      serial_console_height=10,
                      default_baud=115200)

if __name__ == '__main__':
    app.mainloop()
