#!/usr/bin/env python3

import sys
sys.path.append("src")

from tkinter import *
from tkinter.messagebox import showerror

import manager
import gui
import plot
import time
import enum

class Config(enum.Enum):
    DEMO = 0
    MK_1 = 1
    MK_2 = 2

def vector_DataType(name, *args, **kwd_args):
    data_types = [manager.DataType(d + "_" + name, *args, **kwd_args) for d in ['x', 'y', 'z']]
    data_types.append(manager.PacketSpec(name, *data_types))
    return data_types

def init(config=Config.MK_1):
    dts =\
        [manager.DataType('run_time', int, units="ms", show=False, export_csv=False),
         manager.DataType('force', float, units="Newtons", export_csv=True),
         manager.DataType('inlet_temperature', float, units="deg C", export_csv=True),
         manager.DataType('outlet_temperature', float, units="deg C", export_csv=True)] +\
         ([] if config != Config.MK_2 else
          [manager.DataType('chamber_temperature', float, units="deg C", export_csv=True),
           manager.DataType('pressure', float, units="PSI", export_csv=True)]) +\
        vector_DataType('acceleration', float, units="m/s^2", export_csv=True) +\
        [manager.DataType('status', str, show=False),
         # True = open, False = closed for these
         manager.DataType('sensor_status', bool, show=False),
         manager.DataType('fuel_pre_setting', bool, show=False),
         manager.DataType('oxy_pre_setting', bool, show=False),
         manager.DataType('fuel_main_setting', bool, show=False),
         manager.DataType('oxy_main_setting', bool, show=False)]
    plots =\
        [plot.Plot('time', 'force', width=3, show_x_label=False)] +\
        ([] if config != Config.MK_2 else
         [plot.Plot('time', 'pressure', width=3),
          plot.Plot('time', 'chamber_temperature')]) +\
        [plot.Plot('time', ['inlet_temperature', 'outlet_temperature'], "temperature",
                   width=3 if config != Config.MK_2 else 1, show_x_label=False),
         plot.Plot('time', ['x_acceleration', 'y_acceleration', 'z_acceleration'],
                   width=3 if config != Config.MK_2 else 1)]
    dispatcher = manager.Dispatcher(*dts)
    data_manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, data_manager, plots, master=root,
                          window_manager_title=
                          "Telemetry monitor - Demo static test" if config == Config.DEMO else
                          "Telemetry monitor - Mk 1 static test" if config == Config.MK_1 else
                          "Telemetry monitor - Mk 2 static test" if config == Config.MK_2 else
                          "Telemetry monitor",
                          show_send_value=False,
                          serial_console_height=5,
                          default_baud=115200)
    running = False
    def start_abort_handler():
        nonlocal running
        if running:
            app.sendValue("stop")
        else:
            app.reset()
            if app.start():
                app.sendValue("start")
                running = True

    def check_stop(time, status):
        nonlocal running
        if status == 'STAND_BY':
            app.stop()
            running = False
            if config == Config.DEMO:
                countdown.config(text="  T-00:10:00")
            else:
                countdown.config(text="  T-01:00:00")
            start_abort_button.config(text="Start", bg='lime green')
        else:
            start_abort_button.config(text="Abort", bg='red')

    def update_time(abs_time, relative_time):
        if not running:
            relative_time = -60000 if config != Config.DEMO else -10000
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
    Label(app, text="\nControls").pack()
    
    # Sensor controls
    #Label(app, text="\nSensor Controls").pack()
    controlsFrame = Frame(app)
    controlsFrame.pack()
    sensorStatus = Label(controlsFrame, text="All sensors functional", fg='green', font=("Helvetica", 17))
    sensorStatus.pack()
    Button(controlsFrame, text="Zero force", command=lambda: app.sendValue("zero_force")).pack(side=LEFT)
    if config == Config.MK_2:
        Button(controlsFrame, text="Zero pressure", command=lambda: app.sendValue("zero_pressure")).pack(side=LEFT)
    Button(controlsFrame, text="Reset board", command=lambda: app.sendValue("reset")).pack(side=LEFT)

    # Throttle controls
    #Label(app, text="\nThrottle Controls").pack()
    throttleFrame = Frame(app)
    throttleFrame.pack()
    Label(throttleFrame, text="Prestage", font=("Helvetica", 15)).grid(row=0, column=1)
    Label(throttleFrame, text="Mainstage", font=("Helvetica", 15)).grid(row=0, column=2, padx=15)
    Label(throttleFrame, text="Fuel", font=("Helvetica", 15)).grid(row=1, column=0, sticky=W, padx=5)
    Label(throttleFrame, text="Oxygen", font=("Helvetica", 15)).grid(row=2, column=0, sticky=W, padx=5)

    valves = ['fuel_pre', 'fuel_main', 'oxy_pre', 'oxy_main']
    valveSettings = {valve: False for valve in valves}
    valveButtons = {}
    for i, valve in enumerate(valves):
        button = Button(throttleFrame, text="closed", background="red")
        button.bind('<Button-1>', lambda _: app.sendValue(valve + "_command", not valveSettings[valve]))
        button.grid(row=1 + i % 2, column=1 + int(i / 2), sticky=W, padx=5)
        valveButtons[valve] = button

    # Run controls
    #Label(app, text="\nRun Controls").pack()
    runFrame = Frame(app)
    runFrame.pack()
    start_abort_button = Button(runFrame, text="Start", command=start_abort_handler, bg="lime green", height=3, width=10)
    start_abort_button.pack(side=LEFT)
    countdown = Label(runFrame, text="  T-01:00:00", fg="red", font=("Helvetica", 20, "bold"))
    countdown.pack()
    status = Label(runFrame, text="  Stand by", width=15, font=("Helvetica", 17))
    status.pack()

    # Listeners
    app.dispatcher.add_listener('status', lambda time, val: status.config(text="  " + state_name(val)))
    app.dispatcher.add_listener('status', check_stop)
    app.dispatcher.add_listener('run_time', update_time)
    app.dispatcher.add_listener('sensor_status', lambda time, val: sensorStatus.config(text="All sensors functional" if val else "Sensor error encountered",
                                                                                       fg='green' if val else 'red'))

    for valve in valves:
        def callback(time, val):
            valveSettings[valve] = val
            valveButtons.config(text='open' if val else 'closed', background='green' if val else 'red')
        app.dispatcher.add_listener(valve + '_setting', callback)

    return app

if __name__ == '__main__':
    init().mainloop()
