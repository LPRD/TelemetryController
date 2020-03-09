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
    FLIGHT = 2

def vector_DataType(name, *args, **kwd_args):
    data_types = [manager.DataType(d + "_" + name, *args, **kwd_args) for d in ['x', 'y', 'z']]
    data_types.append(manager.PacketSpec(name, *data_types))
    return data_types

def vector_Plot(x, y, name=None, *args, **kwd_args):
    if name == None:
        name = y.replace("_", " ")
    return plot.Plot(x, [d + "_" + y for d in ['x', 'y', 'z']], name, *args, **kwd_args)


def init(config=Config.FLIGHT):
    dts = (
           [
           manager.DataType('bmp_alt', float, units='m', thresholds=(-100, 80000)),
           manager.DataType('gps_alt', float, units='m', thresholds=(-100, 80000)),
           manager.DataType('gps_lat', float, units='deg', thresholds=(-91, 91)),
           manager.DataType('gps_lon', float, units='deg', thresholds=(-181, 181)),
           manager.DataType('vb1', float, units='V', thresholds=(-1, 55)),
           manager.DataType('test', float, units='_', thresholds=(-1, 1)),
           manager.DataType('hdp', float, units='m', thresholds=(0, 100)),
           manager.DataType('sats', int, units='#', thresholds=(-10, 169)),
           manager.DataType('heading', float, units='deg', thresholds=(-180, 180)),
           manager.DataType('attitude', float, units='deg', thresholds=(-90, 90)),
           manager.DataType('bank', float, units='deg', thresholds=(-180, 180))
           ] +
           vector_DataType('euler_angle', float, units='degrees', thresholds=(-180, 360)) +
           vector_DataType('magnetometer', float, units='mu T', thresholds=(-100, 100)) +
           vector_DataType('gyro', float, units='rad/s', thresholds=(-100, 100)) +
           vector_DataType('acceleration', float, units='m/sec^2', thresholds=(-50, 50)) +
           [
           manager.DataType('temperature', float, units='deg C', thresholds=(-20, 80)),
           manager.DataType('gps_vel', float, units='xy m/s', thresholds=(-20, 100)),
           manager.DataType('gps_dir', float, units='xy deg', thresholds=(-20, 365)),
           manager.DataType('xy_from_lanch', float, units='xy m', thresholds=(-20, 100000)),
           manager.DataType('dir_from_launch', float, units='xy deg', thresholds=(-20, 365)),
           manager.DataType('run_time', int, units="ms", show=False, export_csv=False),
           manager.DataType('status', str),
           manager.DataType('P1_setting', bool),
           manager.DataType('P2_setting', bool),
           manager.DataType('P3_setting', bool),
           manager.DataType('P4_setting', bool),
           manager.DataType('P5_setting', bool),
           manager.DataType('l2g', bool, show=False),
           manager.DataType('ss', bool, show=False) #sensor_status
           ]
           )
    plots = [plot.Plot('time', ['bmp_alt', 'gps_alt'], "Altitude", width=2, show_x_label=False),
             plot.Plot('time', ['heading', 'attitude','bank'], "q-Angles", width=4, show_x_label=False),
             plot.Plot('time', 'gps_lat', width=1, show_x_label=False),
             plot.Plot('time', 'gps_lon', width=1, show_x_label=False),
             vector_Plot('time', 'gyro', width=4, show_x_label=False),
             vector_Plot('time', 'euler_angle', width=4, show_x_label=False),
             vector_Plot('time', 'acceleration', width=4, show_x_label=False)]
    dispatcher = manager.Dispatcher(*dts)
    data_manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, data_manager, plots, master=root,
                           window_manager_title=
                           "Telemetry monitor - Demo" if config == Config.DEMO else
                           "Telemetry monitor - Flight" if config == Config.FLIGHT else
                           "Telemetry monitor",
                           show_send_value=False,
                           serial_console_height=8,
                           default_baud=57600)

    running = False
    def heartbeat():
        if running:
            app.sendValue("c")  #c stands for connection, i.e. heartbeat
            app.after(500, heartbeat)

    def start_abort_handler():
        nonlocal running
        if running:
            app.sendValue("a")  #a= abort
        else:
            app.reset()
            if app.start():
                app.sendValue("s")  #s=start
                running = True
                heartbeat()

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
    Button(controlsFrame, text="Zero pressure", command=lambda: app.sendValue("zero_pressure")).pack(side=LEFT)
    Button(controlsFrame, text="Reset board", command=lambda: app.sendValue("reset")).pack(side=LEFT)
    #BMP_cf - pressure calibration factor input
    #Launch_ALT
    #ATST
    #launch_lat
    #launch_lon
    #land_lat
    #land_lon

    updateFrame= Entry(app)
    updateFrame.pack()
    updateFrame.focus_set()  #not sure if this is needed

    def sendVar():





    # Igniter controls- can only switch one way...
    #Label(app, text="\Igniter Controls").pack()
    #igniterFrame = Frame(app)
    #igniterFrame.pack()
    #fireButton = Button(igniterFrame, text="Camera", background="orange", command=lambda: app.sendValue("cam"))
    #fireButton.pack()

    # Throttle controls
    #Label(app, text="\nThrottle Controls").pack()
    throttleFrame = Frame(app)
    throttleFrame.pack()
    Label(throttleFrame, text="Drouge", font=("Helvetica", 15)).grid(row=0, column=1)
    Label(throttleFrame, text="Main", font=("Helvetica", 15)).grid(row=0, column=2, padx=15)
    Label(throttleFrame, text="1", font=("Helvetica", 15)).grid(row=1, column=0, sticky=W, padx=5)
    Label(throttleFrame, text="2", font=("Helvetica", 15)).grid(row=2, column=0, sticky=W, padx=5)

    valves = ['P1', 'P2', 'P3', 'P4']
    valveSettings = {valve: False for valve in valves}
    valveButtons = {}
    for i, valve in enumerate(valves):
        button = Button(throttleFrame, text="closed", background="red")
        button.bind('<Button-1>', lambda _, valve=valve: app.sendValue(valve + "cmd", not valveSettings[valve]))
        button.grid(row=1 + int(i / 2), column=1 + i % 2, sticky=W, padx=5)
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
    app.dispatcher.add_listener('ss', lambda time, val: sensorStatus.config(text="All sensors functional" if val else "Sensor error encountered",
                                                                                       fg='green' if val else 'red'))

    for valve in valves:
        def callback(time, val, valve=valve):
            valveSettings[valve] = val
            valveButtons[valve].config(text='open' if val else 'closed', background='green' if val else 'red')
        app.dispatcher.add_listener(valve + '_setting', callback)

    return app

if __name__ == '__main__':
    init().mainloop()
