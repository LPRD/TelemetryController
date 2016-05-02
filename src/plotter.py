
import tkinter # GUI

import matplotlib.pyplot as plt
plt.ion()
class DynamicUpdatePlot:
    def __init__(self, manager, datatype):
        self.manager = manager
        self.datatype = datatype

        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], '-')
        self.ax.set_xlabel('time (ms)')
        self.ax.set_ylabel(datatype.name)
        #Autoscale on axis
        self.ax.set_autoscalex_on(True)
        self.ax.set_autoscaley_on(True)
        #Other stuff
        self.ax.grid()

        manager.add_listener(datatype.name, self.get_listener())

    def get_listener(self):
        def fn(xdata, ydata):
            #Update data (with the new _and_ the old points)
            self.lines.set_xdata(xdata)
            self.lines.set_ydata(ydata)
            #Need both of these in order to rescale
            self.ax.relim()
            self.ax.autoscale_view()
            #We need to draw *and* flush
            self.figure.canvas.draw()
            self.figure.canvas.flush_events()
        return fn
