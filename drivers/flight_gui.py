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
    return plot.Plot(x, [d + "_" + y for d in ['x', 'y', 'z']], name, *args, **kwd_args)

dts = ([manager.DataType('temperature', float, units='deg C', thresholds=(-20, 80))] +
       vector_DataType('magnetometer', float, thresholds=(-100, 100)) + # TODO: units
       vector_DataType('gyro', float, thresholds=(-100, 100)) + # TODO: units
       vector_DataType('euler_angle', float, units='degrees', thresholds=(0, 360)) +
       vector_DataType('acceleration', float, units='m/sec^2', thresholds=(-50, 50)))
plots = [vector_Plot('time', 'magnetometer', width=4),
         vector_Plot('time', 'gyro', width=4),
         vector_Plot('time', 'euler_angle', width=4),
         vector_Plot('time', 'acceleration', width=4)]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      console_height=10)

if __name__ == '__main__':
    app.mainloop()
