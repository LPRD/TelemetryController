#!/usr/bin/python3

from tkinter import *

import manager
import gui

if __name__ == '__main__':
    dt1 = manager.DataType('force', float, units='Newtons')
    dispatcher = manager.Dispatcher(dt1)
    manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, manager, master=root)
    app.mainloop()
