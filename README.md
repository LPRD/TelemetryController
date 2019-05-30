# Telemetry Controller
Python matplotlib-based graphical viewer for telemetry streams

## Arduino setup instructions
To communicate in the standard packet format, a basic arduino library containing some utility macros is provided.  To install, download libs/Telemetry.  In the arduino software, select Sketch->Include Library->Add .ZIP Library... and select to the downloaded zip file.  

## GUI setup instructions
### Method 1 - run-only, no development
Do this if you only want to run the program and won't need to make any changes to the source.  
You can simply download the packaged executables under dist, which should run with no extra dependencies.  Use the .exe binaries on Windows, or the binaries with no extension on Mac and Linux

### Method 2 - setup for development
TODO: Re-write this, since virtualenv was removed

## TODO items
### Enhancements
* Proper support for shared x axis
* Change default icon
* Access to advanced plot features (axis sharing in plots?)
* Hide value readout scrollbar when unneeded
* Check if saved before exiting?
* Better error messages for CSV parse failure

### Known issues
* Fix CSV exporter dialog behavior on failure to select a file name
* Slowdown when plotting has been running for a while
* Large numbers of invalid packets until restart after certain disruptions (reproduce?)
* Serial ports under WINE act like Linux serial ports, preventing testing
* Fix glitchy scrollbar on value readout - convert to TreeView?
* Convert comments to docstrings

### Fix later
* Create new folder from save dialogue
  * Not easily possible with tk file dialogs
