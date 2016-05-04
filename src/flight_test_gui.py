#!/usr/bin/env python3

from tkinter import *

import manager
import gui

if __name__ == '__main__':
    dts = [#manager.DataType('temperature', float, plot=True, units='deg C'),
           manager.DataType('x', float, plot=True, units='Gs'),
           manager.DataType('y', float, plot=True, units='Gs'),
           manager.DataType('z', float, plot=True, units='Gs')]
    dispatcher = manager.Dispatcher(*dts)
    manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, manager, master=root)
    app.mainloop()
