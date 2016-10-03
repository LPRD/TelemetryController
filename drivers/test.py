#!/usr/bin/env python3

import manager
import serialmanager
import plotter

if __name__ == '__main__':
    dt1 = manager.DataType('test1', int)
    dt2 = manager.DataType('test2', float, units="foo")
    dt3 = manager.DataType('test3', str, False)
    dt4 = manager.DataType('test4', float)
    dt5 = manager.DataType('test5', str, False)
    dt6 = manager.DataType('test6', float)
    dt7 = manager.DataType('test7', float)
    dt8 = manager.DataType('test8', float)
    d = manager.Dispatcher(dt1, dt2, dt3, dt4, dt5, dt6, dt7, dt8)
    m = manager.DataManager(d)
    plot1 = plotter.DynamicUpdatePlot(m, dt6)
    plot2 = plotter.DynamicUpdatePlot(m, dt8)
    serial_in = serialmanager.SerialManager(d, serialmanager.serial_ports()[0])
    
    m.start()
    while True:
        serial_in.handleInput()
        m.update_all_listeners()
