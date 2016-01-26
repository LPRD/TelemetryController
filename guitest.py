#!/usr/bin/python3

from tkinter import *

import manager
import gui

if __name__ == '__main__':
    dt1 = manager.DataType('test1', int)
    dt2 = manager.DataType('test2', float)
    dt3 = manager.DataType('test3', str, False)
    manager = manager.DataManager(dt1, dt2, dt3)
    root = Tk()
    app = gui.Application(manager, master=root)
    app.mainloop()
