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
       [manager.DataType('bmp_alt', float, units='m', thresholds=(-100, 80000))] +
       [manager.DataType('gps_alt', float, units='m', thresholds=(-100, 80000))] +
       [manager.DataType('gps_lat', float, units='deg', thresholds=(-91, 91))] +
       [manager.DataType('gps_lon', float, units='deg', thresholds=(-181, 181))] +
       [manager.DataType('gps_vel', float, units='xy m/s', thresholds=(-20, 100))] +
       [manager.DataType('gps_dir', float, units='xy deg', thresholds=(-20, 365))] +
       [manager.DataType('xy_from_lanch', float, units='xy m', thresholds=(-20, 100000))] +
       [manager.DataType('dir_from_launch', float, units='xy deg', thresholds=(-20, 365))] +
       [manager.DataType('sats', float, units='#', thresholds=(-10, 169))] +
       vector_DataType('magnetometer', float, units='mu T', thresholds=(-100, 100)) +
       vector_DataType('gyro', float, units='rad/s', thresholds=(-100, 100)) +
       vector_DataType('euler_angle', float, units='degrees', thresholds=(0, 360)) +
       vector_DataType('acceleration', float, units='m/sec^2', thresholds=(-50, 50)))
plots = [plot.Plot('time', ['bmp_alt', 'gps_alt'], "Altitude", width=2, show_x_label=False),
         plot.Plot('time', 'gps_lat', width=1, show_x_label=False),
         plot.Plot('time', 'gps_lon', width=1, show_x_label=False),
         vector_Plot('time', 'gyro', width=4),
         vector_Plot('time', 'euler_angle', width=4),
         vector_Plot('time', 'acceleration', width=4)]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      serial_console_height=10,
                      default_baud=57600)

if __name__ == '__main__':
    app.mainloop()
