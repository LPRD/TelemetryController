#!/usr/bin/python3

import manager
import serialinput
import plotter

if __name__ == '__main__':
    dt = manager.DataType('test', int)
    m = manager.DataManager(dt)
    plot = plotter.DynamicUpdatePlot(dt, m)
    serial_in = serialinput.SerialReader(m)
    serial_in.start()
