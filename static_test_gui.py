#!/usr/bin/python3

from tkinter import *
from tkinter.messagebox import showerror

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
    app = gui.Application(dispatcher, manager, master=root, show_send_value=False)

    # Add custom gui controls
    Label(app, text="\nMisc Controls").pack()
    controlsFrame = Frame(app)
    controlsFrame.pack()
    def writeZero():
        if app.serialManager:
            app.serialManager.write("@@@@@:zero:&&&&&\r\n")
        else:
            showerror("Error", "No serial port selected")
    zeroButton = Button(controlsFrame, text="Zero", command=writeZero)
    zeroButton.pack(side=LEFT)

    app.mainloop()
