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
    MK_2 = 2

def vector_DataType(name, *args, **kwd_args):
    data_types = [manager.DataType(d + "_" + name, *args, **kwd_args) for d in ['x', 'y', 'z']]
    data_types.append(manager.PacketSpec(name, *data_types))
    return data_types

NUM_MK2_THERMOCOUPLES = 3

##UPDATED##
##TODDO: ADD new data types so that the gui can communicate with the arduino##
def init(config=Config.MK_2):
    dts =\
        [manager.DataType('run_time', int, units="ms", show=False, export_csv=False),
         manager.DataType('force1', float, units="Newtons", export_csv=True),
         manager.DataType('force2', float, units="Newtons", export_csv=True),
         manager.DataType('force3', float, units="Newtons", export_csv=True),
         manager.DataType('force4', float, units="Newtons", export_csv=True),
         manager.DataType('inlet_temp', float, units="deg C", export_csv=True),
         manager.DataType('outlet_temp', float, units="deg C", export_csv=True)] +\
         ([] if config != Config.MK_2 else
          [manager.DataType('chamber_temp_' + str(i + 1), float, units="deg C", export_csv=True)
           for i in range(NUM_MK2_THERMOCOUPLES)]) +\
        [manager.DataType('fuel_press', float, units="PSI", export_csv=True),
         manager.DataType('ox_press', float, units="PSI", export_csv=True),
         manager.DataType('fuel_inj_press', float, units="PSI", export_csv=True),
         manager.DataType('ox_inj_press', float, units="PSI", export_csv=True)] +\
        vector_DataType('accel', float, units="m/s^2", export_csv=True) +\
        [manager.DataType('status', str, show=False),
         # True = open, False = closed for these
         manager.DataType('sensor_status', bool, show=False),
         manager.DataType('fuel_pre_setting', bool, show=False),
         manager.DataType('ox_pre_setting', bool, show=False),
         manager.DataType('fuel_main_setting', bool, show=False),
         manager.DataType('ox_main_setting', bool, show=False),
         manager.DataType('nitro_fill_setting', bool, show=False),
         manager.DataType('nitro_drain_setting', bool, show=False)]
    plots =\
        [plot.Plot('time', ['force1','force2','force3','force4'],'force', width=1, show_x_label=False),
         plot.Plot('time', ['fuel_press', 'ox_press', 'fuel_inj_press', 'ox_inj_press'], "line pressure", width=1, show_x_label=False)] +\
        ([] if config != Config.MK_2 else
         [plot.Plot('time', ['chamber_temp_' + str(i + 1)
                             for i in range(NUM_MK2_THERMOCOUPLES)],
                    "chamber temperature")]) +\
        [plot.Plot('time', ['inlet_temp', 'outlet_temp'], "coolant temperature",
                   width=3 if config != Config.MK_2 else 1)]
        #  plot.Plot('time', ['x_accel', 'y_accel', 'z_accel'],
        #            width=3 if config != Config.MK_2 else 1)]
    dispatcher = manager.Dispatcher(*dts)
    data_manager = manager.DataManager(dispatcher)
    root = Tk()
    app = gui.Application(dispatcher, data_manager, plots, master=root,
                          window_manager_title=
                          "Telemetry monitor - Demo static test" if config == Config.DEMO else
                          "Telemetry monitor - Mk 2 static test" if config == Config.MK_2 else
                          "Telemetry monitor",
                          show_send_value=False,
                          serial_console_height=7,
                          default_baud=115200)
    running = False
    def heartbeat():
        if running:
            app.sendValue("heartbeat")
            app.after(500, heartbeat)
    
    def start_abort_handler():
        nonlocal running
        if running:
            app.sendValue("stop")
        else:
            app.reset()
            if app.start():
                app.sendValue("start")
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

    # Igniter controls
    #Label(app, text="\Igniter Controls").pack()
    igniterFrame = Frame(app)
    igniterFrame.pack()
    fireButton = Button(igniterFrame, text="Fire Igniter", background="orange", command=lambda: app.sendValue("fire_igniter"))
    fireButton.pack()

    # Throttle controls
    #Label(app, text="\nThrottle Controls").pack()
    throttleFrame = Frame(app)
    throttleFrame.pack()
    ##UPDATED##
    Label(throttleFrame, text="Fuel", font=("Helvetica", 12)).grid(row=0, column=1)
    Label(throttleFrame, text="Oxidizer", font=("Helvetica", 12)).grid(row=0, column=2)
    Label(throttleFrame, text="Nitrogen", font=("Helvetica", 12)).grid(row=0, column=4, padx=15)
    Label(throttleFrame, text="Prestage", font=("Helvetica", 12)).grid(row=1, column=0, sticky=W)
    Label(throttleFrame, text="Mainstage", font=("Helvetica", 12)).grid(row=2, column=0, sticky=W)
    Label(throttleFrame, text="Fill", font=("Helvetica", 12)).grid(row=1, column=3, padx=5)
    Label(throttleFrame, text="Drain", font=("Helvetica", 12)).grid(row=2, column=3, padx=5)


    ##UPDATED##
    valves = ['fuel_pre', 'ox_pre', 'fuel_main', 'ox_main', 'nitro_fill', 'nitro_drain']
    valveSettings = {valve: False for valve in valves}
    valveButtons = {}
    for i, valve in enumerate(valves):
        button = Button(throttleFrame, text="closed", background="red")
        button.bind('<Button-1>', lambda _, valve=valve: app.sendValue(valve + "_command", not valveSettings[valve]))
        button.grid(row=1 + int(i / 3), column=list([1,2,4])[i % 3], sticky=W, padx=5)
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
        def callback(time, val, valve=valve):
            valveSettings[valve] = val
            valveButtons[valve].config(text='open' if val else 'closed', background='green' if val else 'red')
        app.dispatcher.add_listener(valve + '_setting', callback)
        
    return app

if __name__ == '__main__':
    init().mainloop()
