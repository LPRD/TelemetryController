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
running = False
def start_abort_handler():
    global start_time, running
    if running:
        app.sendValue("stop")
    else:
        app.reset()
        if app.start():
            running = True
            app.sendValue("start")

def check_stop(time, status):
    global running
    if status == 'Manual control':
        app.stop()
        running = False
        countdown.config(text="  T-01:00:00")
        start_abort_button.config(text="Start", bg='lime green')
    else:
        start_abort_button.config(text="Abort", bg='red')

def update_time(abs_time, relative_time):
    if not running:
        relative_time = -60000
    sign = "+" if relative_time > 0 else "-"
    mins = abs(relative_time) // 60000
    secs = (abs(relative_time) // 1000) % 60
    cs   = (abs(relative_time) // 10) % 100
    text = "  T{}{:02}:{:02}:{:02}".format(sign, mins, secs, cs)
    countdown.config(text=text, fg = "green" if relative_time > 0 else "red")


# Add custom gui controls
Label(app, text="\nSensor Controls").pack()
controlsFrame = Frame(app)
controlsFrame.pack()
Button(controlsFrame, text="Zero force sensor", command=lambda: app.sendValue("zero")).pack(side=LEFT)
Label(app, text="\nRun Controls").pack()
runFrame = Frame(app)
runFrame.pack()

start_abort_button = Button(runFrame, text="Start", command=start_abort_handler, bg="lime green", height=3, width=10)
start_abort_button.pack(side=LEFT)
countdown = Label(runFrame, text="  T-01:00:00", fg="red", font=("Helvetica", 20, "bold"))
countdown.pack()
status = Label(runFrame, text="  Manual control", width=15, font=("Helvetica", 17))
status.pack()

app.dispatcher.add_listener('status', lambda time, val: status.config(text="  " + val))
app.dispatcher.add_listener('status', check_stop)
app.dispatcher.add_listener('run_time', update_time)

if __name__ == '__main__':
    app.mainloop()
