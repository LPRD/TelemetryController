#!/usr/bin/python3

from tkinter import *

import manager
import gui

if __name__ == '__main__':
    dts = [manager.DataType('force', float, units='Newtons'),
           manager.DataType('temperature', float, units='deg C'),
           manager.DataType('x', float, units='Gs', plot=False),
           manager.DataType('y', float, units='Gs', plot=False),
           manager.DataType('z', float, units='Gs', plot=False)]
    dispatcher = manager.Dispatcher(*dts)
    manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, manager, master=root)
    app.mainloop()
