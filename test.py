#!/usr/bin/python3

import manager
import serialinput
import plotter

if __name__ == '__main__':
    dt1 = manager.DataType('test1', int)
    dt2 = manager.DataType('test2', float)
    dt3 = manager.DataType('test3', str)
    m = manager.DataManager(dt1, dt2, dt3)
    plot1 = plotter.DynamicUpdatePlot(m, dt1)
    plot2 = plotter.DynamicUpdatePlot(m, dt2)
    serial_in = serialinput.SerialReader(m)
    serial_in.start()
