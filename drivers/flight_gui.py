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
           manager.DataType('run_time', int, units="ms"),
           manager.DataType('Launch_ALT', float, units="m"),
           manager.DataType('Px', float, units='m'), #E/W
           manager.DataType('Py', float, units='m'), #N/S
           manager.DataType('Pz', float, units='m'), #AGL       #Kalman Altitude AGL
           manager.DataType('bno_alt', float, units='m'),   #Kalman Altitude ASL
           manager.DataType('bmp_alt', float, units='m', thresholds=(-100, 80000)),
           manager.DataType('gps_alt', float, units='m', thresholds=(-100, 80000)),
           manager.DataType('x_from_launch', float, units='xy m', thresholds=(-10000, 100000)),
           manager.DataType('y_from_launch', float, units='xy m', thresholds=(-10000, 100000)),
           manager.DataType('dir_from_launch', float, units='xy deg', thresholds=(-20, 365)),
           manager.DataType('gps_lat', float, units='deg', show=False, thresholds=(-91, 91)),
           manager.DataType('gps_lon', float, units='deg', show=False, thresholds=(-181, 181)),
           manager.DataType('launch_lat', float, show=False),
           manager.DataType('launch_lon', float, show=False),
           manager.DataType('vb1', float, units='V', thresholds=(-1, 55)),
           #manager.DataType('test', float, thresholds=(-1, 1)),
           manager.DataType('hdp', float, units='m', thresholds=(0, 100)),
           manager.DataType('sats', int, units='#', thresholds=(-10, 169)),
           manager.DataType('roll', float, units='deg', thresholds=(-180, 180)),    #phi, body x
           manager.DataType('pitch', float, units='deg', thresholds=(-90, 90)),     #theta, body y
           manager.DataType('yaw', float, units='deg', thresholds=(-180, 180)),      #psy, body z
           manager.DataType('oX', float, units='deg', thresholds=(-180, 180)),    #phi, body x (roll)
           manager.DataType('oY', float, units='deg', thresholds=(-90, 90)),     #theta, body y (pitch)
           manager.DataType('oZ', float, units='deg', thresholds=(-180, 180))      #psy, body z (yaw)
           #manager.DataType('bank', float, units='deg', thresholds=(-180, 180)),    #roll
           #manager.DataType('heading', float, units='deg', thresholds=(-90, 90)),   #pitch
           #manager.DataType('attitude', float, units='deg', thresholds=(-180, 180))   #yaw
           ] +
           #vector_DataType('euler_angle', float, units='degrees', thresholds=(-180, 360)) +
           vector_DataType('magnetometer', float, units='mu T', thresholds=(-100, 100)) +
           vector_DataType('gyro', float, units='rad/s', thresholds=(-100, 100)) +
           vector_DataType('acceleration', float, units='m/sec^2', thresholds=(-50, 50)) +
           [
           manager.DataType('tIMU', float, units='deg C', thresholds=(-20, 80)),
           manager.DataType('gps_vel', float, units='xy m/s', thresholds=(-20, 100)),
           manager.DataType('gps_dir', float, units='xy deg', thresholds=(-20, 365)),
           manager.DataType('P1_setting', bool),
           manager.DataType('P2_setting', bool),
           manager.DataType('P3_setting', bool),
           manager.DataType('P4_setting', bool),
           manager.DataType('P5_setting', bool),

           manager.DataType('ATST', float, units="m"),
           manager.DataType('BMPcf', float, units="HPa"),
           #manager.DataType('land_lat', float),
           #manager.DataType('land_lon', float),
           #manager.DataType('gps_n', float, units="m"),
           #manager.DataType('gps_e', float, units="m"),

           #manager.DataType('up', bool),
           #manager.DataType('down', bool),
           #manager.DataType('gps_d', bool),
           #manager.DataType('bmp_d', bool),
           #manager.DataType('bmp_d2', bool),
           #manager.DataType('bno_d', bool),

           manager.DataType('status', str), #str),
           manager.DataType('Apogee_Passed', bool),
           manager.DataType('l2g', bool),
           manager.DataType('ss', bool) #sensor_status , show=False
           ]
           )
    plots = [plot.Plot('time', 'Px', width=1, show_x_label=False),
             plot.Plot('time', 'Py', width=1, show_x_label=False),
             plot.Plot('Px', ['Py'], "X/Y pos", width=2, height=2, show_x_label=False),
             plot.Plot('time', ['bmp_alt', 'gps_alt', 'bno_alt'], "Alt ASL", width=2, height=1, show_x_label=False),
             plot.Plot('time', ['roll', 'pitch','yaw'], "Fusion q-Angles", width=2, height=1, show_x_label=False),
             #vector_Plot('time', 'euler_angle', width=4, show_x_label=False),
             plot.Plot('time', ['oX', 'oY','oZ'], "Gyro Orientation", width=2, height=1, show_x_label=False),
             vector_Plot('time', 'gyro', width=2, show_x_label=False),
             vector_Plot('time', 'acceleration', width=2, height=1, show_x_label=False)]
    dispatcher = manager.Dispatcher(*dts)
    data_manager = manager.DataManager(dispatcher)
    root = Tk()
    root.configure(background='#69615e')
    app = gui.Application(
        dispatcher, data_manager, plots, master=root,
        window_manager_title=
        "Telemetry monitor - Demo" if config == Config.DEMO else
        "Telemetry monitor - Cricket" if config == Config.FLIGHT else
        "Telemetry monitor",
        show_send_value=False,
        serial_console_height=1,
        plots_size=(10,10),
        plots_background='#69615e',
        controls_background='#69615e',
        default_baud=57600)

    running = False
    def heartbeat():
        if running:        #get link2ground status all the time, exept if I delete this line, the start/abort button doesn't work right for some reason
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
        if status == 'STAND_BY':    #was 'STAND_BY'
            #status.config(bg='#0fe9f5')
            app.stop()
            running = False
            if config == Config.DEMO:
                countdown.config(text="  T-00:10:00")
            else:
                countdown.config(text="  T-01:00:00")
            start_abort_button.config(text="Start", bg='lime green')
        #I figured it out... having the below code included caused the unresponsiveness :(

        #elif status == 'TERMINAL_COUNT':
        #    status.config(bg='#e6d925')            #status.config is bad specifically!!!!
        #elif status == 'POWERED_ASCENT':
        #    status.config(bg='#e04122')

        #elif status == 'UNPOWERED_ASCENT':
        #    status.config(bg='#bd857b')
        #elif status == 'FREEFALL':
        #    status.config(bg='#760e99')
        #elif status == 'DROGUE_DESCENT':
        #    status.config(bg='#8b65ba')
        #elif status == 'MAIN_DESCENT':
        #    status.config(bg='#402aa1')
        #elif status == 'LANDED':
        #    status.config(bg='#4395d9')

        else:
            start_abort_button.config(text="Abort", bg='red')
        #if status == 'TERMINAL_COUNT':
        #    running = True
            #qqq= 10            #causes issues also


    def update_time(abs_time, relative_time):
        if not running:
            relative_time = -60000 if config != Config.DEMO else -10000
        sign = "+" if relative_time > 0 else "-"
        mins = abs(relative_time) // 60000
        secs = (abs(relative_time) // 1000) % 60
        cs   = (abs(relative_time) // 10) % 100
        text = "  T{}{:02}:{:02}:{:02}".format(sign, mins, secs, cs)
        countdown.config(text=text, fg = "green" if relative_time > 0 else "red")

    #def update_state(time, status):
    #    if status== 'STAND_BY':
    #        status.config(bg='#e6d925')
    #    if status == 'POWERED_ASCENT':
    #        status.config(bg='#e04122')
    #    if status == 'UNPOWERED_ASCENT':
    #        status.config(bg='#bd857b')
    #    if status == 'FREEFALL':
    #        status.config(bg='#760e99')
    #    if status == 'DROGUE_DESCENT':
    #        status.config(bg='#8b65ba')
    #    if status == 'MAIN_DESCENT':
    #        status.config(bg='#402aa1')
    #    if status == 'LANDED':
    #        status.config(bg='#4395d9')




    def state_name(name):
        lower_name = name[0] + name[1:].lower()
        return lower_name.replace("_", " ")

    # Add custom gui controls
    Label(app, text="\nControls", bg= '#69615e').pack(side=TOP)

    # Sensor controls
    #Label(app, text="\nSensor Controls").pack()
    controlsFrame = Frame(app, bg= '#69615e')
    controlsFrame.pack(side=TOP)    #expand=1
    sensorStatus = Label(controlsFrame, text="All sensors functional", fg='green', font=("Helvetica", 12), bg= '#c9c1be') #light grey c9c1be
    sensorStatus.grid(row=0,column=0,columnspan=4)
    #Button(controlsFrame, text="Zero force", command=lambda: app.sendValue("zero_force")).pack(side=LEFT)
    #Button(controlsFrame, text="Zero pressure", command=lambda: app.sendValue("zero_pressure")).pack(side=LEFT)
    #Button(controlsFrame, text="Reset board", command=lambda: app.sendValue("reset")).pack(side=LEFT)
    #BMP_cf - pressure calibration factor input
    #Launch_ALT
    #ATST
    #launch_lat
    #launch_lon
    #land_lat
    #land_lon
    u1= Entry(controlsFrame)    #,width=20
    u1.grid(row=1,column=2,columnspan=2)
    #u1.focus_set()  #not sure if this is needed
    #def sendVar():
    b1= Button(controlsFrame, text="Zero Pz/Set Launch Alt (m)",font=("Helvetica", 7), width=20, command=lambda: app.sendValue("Launch_ALT",float(u1.get())))
    b1.grid(row=1,column=0,padx=5,columnspan=2)

    u2= Entry(controlsFrame)
    u2.grid(row=2,column=2,columnspan=2)
    b2= Button(controlsFrame, text="set BMP calib. factor (HPA)", width=20,font=("Helvetica", 7) , command=lambda: app.sendValue("BMP_cf",u2.get()))
    b2.grid(row=2,column=0,padx=5,columnspan=2)

    u3= Entry(controlsFrame)
    u3.grid(row=3,column=2,columnspan=2)
    b3= Button(controlsFrame, text="set ATST (m)", width=20,font=("Helvetica", 7), command=lambda: app.sendValue("ATST",u3.get()))
    b3.grid(row=3,column=0,padx=5,columnspan=2)

    u4= Entry(controlsFrame,width=8)
    u4.grid(row=4,column=1)
    b4= Button(controlsFrame, text="--(open)--", width=10, font=("Helvetica", 7), command=lambda: app.sendValue("launch_lat",u4.get()))
    b4.grid(row=4,column=0,padx=1)

    u5= Entry(controlsFrame,width=8)
    u5.grid(row=4,column=3)
    b5= Button(controlsFrame, text="--(open)--", font=("Helvetica", 7), width=10, command=lambda: app.sendValue("launch_lon",u5.get()))
    b5.grid(row=4,column=2,padx=1)

    u6= Entry(controlsFrame,width=8)
    u6.grid(row=5,column=1)
    b6= Button(controlsFrame, text="Zero Py", width=10, font=("Helvetica", 7), command=lambda: app.sendValue("0Lat",u6.get()))
    b6.grid(row=5,column=0,padx=1)

    u7= Entry(controlsFrame,width=8)
    u7.grid(row=5,column=3)
    b7= Button(controlsFrame, text="Zero Px", width=10, font=("Helvetica", 7), command=lambda: app.sendValue("0Lon",u7.get()))
    b7.grid(row=5,column=2,padx=1)


    # Igniter controls- can only switch one way...
    #Label(app, text="\Igniter Controls").pack()
    #igniterFrame = Frame(app)
    #igniterFrame.pack()
    #fireButton = Button(igniterFrame, text="Camera", background="orange", command=lambda: app.sendValue("cam"))
    #fireButton.pack()

    # Throttle controls
    #Label(app, text="\nThrottle Controls").pack()
    throttleFrame = Frame(app, bg= '#69615e')   #bg or background works
    throttleFrame.pack()
    Label(throttleFrame, text="Drogue", font=("Helvetica", 10), bg= '#69615e').grid(row=0, column=1, sticky= W)
    Label(throttleFrame, text="Main", font=("Helvetica", 10), bg= '#69615e').grid(row=0, column=2, padx=15, sticky= W)
    Label(throttleFrame, text="1", font=("Helvetica", 10), bg= '#69615e').grid(row=1, column=0, sticky=W, padx=5)
    Label(throttleFrame, text="2", font=("Helvetica", 10), bg= '#69615e').grid(row=2, column=0, sticky=W, padx=5)
    Label(throttleFrame, text="Cam", font=("Helvetica", 10), bg= '#69615e').grid(row=3, column=0, sticky=W, padx=5)
    Button(throttleFrame, text="Reset board", font=("Helvetica", 8), command=lambda: app.sendValue("reset")).grid(row=3, column=2, sticky=W, padx=5)


    valves = ['P1', 'P2', 'P3', 'P4', 'P5']         #indexing starts at 0
    valveSettings = {valve: False for valve in valves}
    valveButtons = {}
    for i, valve in enumerate(valves):
        button = Button(throttleFrame, text="closed", background="red")
        button.bind('<Button-1>', lambda _, valve=valve: app.sendValue(valve + "cmd", not valveSettings[valve]))
        button.grid(row=1 + int(i / 2), column=1 + i % 2, sticky=W, padx=5)
        valveButtons[valve] = button

    # Run controls
    #Label(app, text="\nRun Controls").pack()
    runFrame = Frame(app, bg= '#69615e')
    runFrame.pack(side=TOP)
    start_abort_button = Button(runFrame, text="Start", command=start_abort_handler, bg="lime green", height=2, width=8)
    start_abort_button.pack(side=LEFT)
    countdown = Label(runFrame, text="  T-01:00:00", width=10, fg="red", font=("Helvetica", 16, "bold"), bg= '#c9c1be')  #b9b1ae
    countdown.pack(side=TOP)

    status = Label(runFrame, text="  Stand by", width=16, font=("Helvetica", 10), bg= '#c9c1be')
    status.pack(side=TOP)





    # Listeners
    app.dispatcher.add_listener('status', lambda time, val: status.config(text="  " + state_name(val)))
    app.dispatcher.add_listener('status', check_stop)
    #app.dispatcher.add_listener('status', update_state)
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
