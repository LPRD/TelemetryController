#!/usr/bin/env python3

import sys
sys.path.append("src")

from tkinter import *
from tkinter.messagebox import showerror

import manager
import gui
import plot
import time

def vector_DataType(name, *args, **kwd_args):
    data_types = [manager.DataType(d + "_" + name, *args, **kwd_args) for d in ['x', 'y', 'z']]
    data_types.append(manager.PacketSpec(name, *data_types))
    return data_types

dts =\
    [manager.DataType('run_time', int, units="ms", show=False, export_csv=False),
     manager.DataType('force', float, units="Newtons", export_csv=True),
     manager.DataType('inlet_temperature', float, units="deg C", export_csv=True),
     manager.DataType('outlet_temperature', float, units="deg C", export_csv=True)] +\
    vector_DataType('acceleration', float, units="Gs", export_csv=True) +\
    [manager.DataType('status', str, show=False),
     manager.DataType('fuel_control', int, show=False),
     manager.DataType('oxy_control', int, show=False),
     manager.DataType('fuel_safety', bool, show=False),
     manager.DataType('oxy_safety', bool, show=False)]
plots = [plot.Plot('time', 'force', width=3, show_x_label=False),
         plot.Plot('time', ['inlet_temperature', 'outlet_temperature'], "coolant temperature", width=3, show_x_label=False),
         plot.Plot('time', ['x_acceleration', 'y_acceleration', 'z_acceleration'], width=3)]
dispatcher = manager.Dispatcher(*dts)
manager = manager.DataManager(dispatcher)
root = Tk()
app = gui.Application(dispatcher, manager, plots, master=root,
                      show_send_value=False,
                      serial_console_height=5,
                      default_baud=230400)
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
    if status == 'MANUAL_CONTROL':
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

def state_name(name):
    lower_name = name[0] + name[1:].lower()
    return lower_name.replace("_", " ")

# Add custom gui controls
Label(app, text="\nSensor Controls").pack()
controlsFrame = Frame(app)
controlsFrame.pack()
Button(controlsFrame, text="Zero force sensor", command=lambda: app.sendValue("zero")).pack(side=LEFT)

# Throttle displays
Label(app, text="\nThrottle").pack()
throttleFrame = Frame(app)
throttleFrame.pack()
Label(throttleFrame, text="Control", font=("Helvetica", 15)).grid(row=0, column=1)
Label(throttleFrame, text="Safety", font=("Helvetica", 15)).grid(row=0, column=2, padx=15)
Label(throttleFrame, text="Fuel", font=("Helvetica", 15)).grid(row=1, column=0, sticky=W, padx=5)
Label(throttleFrame, text="Oxygen", font=("Helvetica", 15)).grid(row=2, column=0, sticky=W, padx=5)
fuelControl = Label(throttleFrame, text="0", bg='white', font=("Helvetica", 12))
fuelControl.grid(row=1, column=1, sticky=W, padx=5)
fuelSafety = Label(throttleFrame, text="Closed", fg='red', bg='white', font=("Helvetica", 12))
fuelSafety.grid(row=1, column=2, sticky=W, padx=20)
oxyControl = Label(throttleFrame, text="0", bg='white', font=("Helvetica", 12))
oxyControl.grid(row=2, column=1, sticky=W, padx=5)
oxySafety = Label(throttleFrame, text="Closed", fg='red', bg='white', font=("Helvetica", 12))
oxySafety.grid(row=2, column=2, sticky=W, padx=20)

# Countdown controls
Label(app, text="\nRun Controls").pack()
runFrame = Frame(app)
runFrame.pack()
start_abort_button = Button(runFrame, text="Start", command=start_abort_handler, bg="lime green", height=3, width=10)
start_abort_button.pack(side=LEFT)
countdown = Label(runFrame, text="  T-01:00:00", fg="red", font=("Helvetica", 20, "bold"))
countdown.pack()
status = Label(runFrame, text="  Manual control", width=15, font=("Helvetica", 17))
status.pack()

# Listeners
app.dispatcher.add_listener('status', lambda time, val: status.config(text="  " + state_name(val)))
app.dispatcher.add_listener('status', check_stop)
app.dispatcher.add_listener('run_time', update_time)
app.dispatcher.add_listener('fuel_control', lambda time, val: fuelControl.config(text=str(val)))
app.dispatcher.add_listener('oxy_control', lambda time, val: oxyControl.config(text=str(val)))
app.dispatcher.add_listener('fuel_safety', lambda time, val: fuelSafety.config(text="Open" if val else "Closed", fg='green' if val else 'red'))
app.dispatcher.add_listener('oxy_safety', lambda time, val: oxySafety.config(text="Open" if val else "Closed", fg='green' if val else 'red'))

if __name__ == '__main__':
    app.mainloop()
