#!/usr/bin/python3

from tkinter import *

import manager
import gui

if __name__ == '__main__':
    dt1 = manager.DataType('test1', int)
    dt2 = manager.DataType('test2', float, units="foo")
    dt3 = manager.DataType('test3', str, False)
    dt4 = manager.DataType('test4', float)
    dt5 = manager.DataType('test5', str, False)
    dt6 = manager.DataType('test6', float)
    dt7 = manager.DataType('test7', float)
    dt8 = manager.DataType('test8', float)
    manager = manager.DataManager(dt1, dt2, dt3, dt4, dt5, dt6, dt7, dt8)
    root = Tk()
    app = gui.Application(manager, master=root)
    app.mainloop()
