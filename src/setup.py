import sys
from cx_Freeze import *

# Dependencies are automatically detected, but it might need fine tuning.
#build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a console application).
base = "Win32GUI"

setup(name = "TelemetryManager",
      version = "0.1",
      description = "Flight test telemetry gui",
      #options = {"build_exe": build_exe_options},
      executables = [Executable("flight_test_gui.py", base=base)])
