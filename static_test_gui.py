#!/usr/bin/python3

from tkinter import *
from tkinter.messagebox import showerror

import manager
import gui
import time

dts = [manager.DataType('force', float, plot=True, units='Newtons'),
       manager.DataType('temperature', float, plot=True, units='deg C'),
       manager.DataType('x', float, units='Gs'),
       manager.DataType('y', float, units='Gs'),
       manager.DataType('z', float, units='Gs'),
       manager.DataType('run_time', int, units='ms', show=False),
       manager.DataType('status', str, show=False)]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, master=root,
                      show_send_value=False,
                      serial_console_height=5)

# Add custom gui controls
Label(app, text="\nSensor Controls").pack()
controlsFrame = Frame(app)
controlsFrame.pack()
Button(controlsFrame, text="Zero force sensor", command=lambda: app.sendValue("zero")).pack(side=LEFT)
Label(app, text="\nRun Controls").pack()
runFrame = Frame(app)
runFrame.pack()

countdown = Label(runFrame, text="T-01:00:00", fg="red", font=("Helvetica", 20, "bold"))
countdown.pack()
status = Label(runFrame, text="Ready", bg="white", font=("TkDefaultFont", 15))
status.pack()

running = False
def start():
    global start_time
    app.reset()
    if app.start():
        running = True
        app.sendValue("start")

def abort():
    app.sendValue("stop")

def check_stop(time, status):
    if status == 'Ready':
        app.stop()
        running = False

def update_time(abs_time, relative_time):
    sign = "+" if relative_time > 0 else "-"
    mins = abs(relative_time) // 60000
    secs = (abs(relative_time) // 1000) % 60
    cs   = (abs(relative_time) // 10) % 100
    text = "T{}{:02}:{:02}:{:02}".format(sign, mins, secs, cs)
    countdown.config(text=text, fg = "green" if relative_time > 0 else "red")

app.dispatcher.add_listener('status', lambda time, val: status.config(text=val))
app.dispatcher.add_listener('status', check_stop)
app.dispatcher.add_listener('run_time', update_time)

Button(runFrame, text="Start", command=start, bg = "lime green", height=3, width=10).pack(side=LEFT)
Button(runFrame, text="Abort", command=abort, bg = "red", height=3, width=10).pack(side=LEFT)

if __name__ == '__main__':
    app.mainloop()
