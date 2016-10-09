#!/usr/bin/env python3

import sys
sys.path.append("src")

from tkinter import *

import manager
import gui
import plot

def vector_DataType(name, *args, **kwd_args):
    data_types = [manager.DataType(d + "_" + name, *args, **kwd_args) for d in ['x', 'y', 'z']]
    data_types.append(manager.PacketSpec(name, *data_types))
    return data_types

def vector_Plot(x, y, name=None, *args, **kwd_args):
    if name == None:
        name = y.replace("_", " ")
    return plot.Plot(x, [d + "_" + y for d in ['x', 'y', 'z']], *args, **kwd_args)

dts = ([manager.DataType('temperature', float, units='deg C'),
        manager.DataType('missed_deadlines', int)] +
       vector_DataType('magnetometer', float) + # TODO: units
       vector_DataType('gyro', float) + # TODO: units
       vector_DataType('euler_angle', float, units='degrees') +
       vector_DataType('acceleration', float, units='m/sec^2'))
plots = [#plot.Plot('time', 'temperature'),
         vector_Plot('time', 'magnetometer'),
         vector_Plot('time', 'gyro'),
         vector_Plot('time', 'euler_angle'),
         vector_Plot('time', 'acceleration')]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      serial_console_height=10,
                      default_baud=38400)

if __name__ == '__main__':
    app.mainloop()
