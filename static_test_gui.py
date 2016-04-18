#!/usr/bin/python3

from tkinter import *
from tkinter.messagebox import showerror

import manager
import gui
import time

dts = [manager.DataType('force', float, units='Newtons'),
       manager.DataType('temperature', float, units='deg C'),
       manager.DataType('x', float, units='Gs', plot=False),
       manager.DataType('y', float, units='Gs', plot=False),
       manager.DataType('z', float, units='Gs', plot=False)]
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

millis = lambda: int(round(time.time() * 1000))

start_time = None
def start():
    global start_time
    if app.start():
        start_time = millis() + 60 * 1000 # Start at T-1 min
        status.config(text="Terminal count")
        update_time()

def stop():
    global start_time
    start_time = None
    app.stop()
    app.sendValue("stop")
    status.config(text="Ready")
    update_time()

def abort():
    # In case of an abort, leave count and data collection running
    app.sendValue("stop")
    status.config(text="Abort!")
    update_time()

def update_time():
    if start_time == None:
        countdown.config(text="T-01:00:00")
    else:
        relative_time = millis() - start_time
        sign = "+" if relative_time > 0 else "-"
        mins = abs(relative_time) // 60000
        secs = (abs(relative_time) // 1000) % 60
        cs   = (abs(relative_time) // 10) % 100
        text = "T{}{:02}:{:02}:{:02}".format(sign, mins, secs, cs)
        countdown.config(text=text, fg = "green" if relative_time > 0 else "red")

        if status['text'] == "Terminal count" and relative_time >= -10000:
            app.sendValue("start")
            status.config(text="Autosequencer started")
        elif status['text'] == "Autosequencer started" and relative_time >= 0:
            status.config(text="Running")
        elif status['text'] == "Running" and relative_time >= 60000:
            status.config(text="Cool down")
        elif status['text'] == "Cool down" and relative_time >= 60000 * 6:
            stop()

        app.after(50, update_time)

Button(runFrame, text="Start", command=start, bg = "lime green", height=3, width=10).pack(side=LEFT)
Button(runFrame, text="Abort", command=abort, bg = "red", height=3, width=10).pack(side=LEFT)

if __name__ == '__main__':
    app.mainloop()
