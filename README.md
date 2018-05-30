# Telemetry-display
Python matplotlib-based graphical viewer for telemetry streams

## Arduino setup instructions
To communicate in the standard packet format, a basic arduino library containing some utility macros is provided.  To install, download libs/Telemetry.  In the arduino software, select Sketch->Include Library->Add .ZIP Library... and select to the downloaded zip file.  

## GUI setup instructions
### Method 1 - run-only, no development
Do this if you only want to run the program and won't need to make any changes to the source.  
You can simply download the packaged executables under dist, which should run with no extra dependencies.  Use the .exe binaries on Windows, or the binaries with no extension on Mac and Linux

### Method 2 - setup for development
#### Linux and Mac
**There is now no need to install python or any libraries!**  Everything should be included in the virtual python env.  To use it,
simply run  
```> source build_tools/linux_venv/bin/activate```
from your shell.  This will load the enclosed instance of python along with the needed libraries.  Then you can simply run the gui scripts directly  
```> src/static_test_gui```  
Note that any python libraries installed via pip with the virtual env activated will be installed to the virtual env.

I recommend that you install UPX (can be found in package upx-ucl on Ubuntu) which will slightly compress executable sizes.  

#### Windows
**Note**: It should be possible to use the virtual python env for development on Windows, but I haven't gotten a chance to test this yet.

1. Install a recent (3.4+) version of python for windows.  Make sure to check the box to add python and pip to your path
2. From cmd, install matplotlib, pyserial and typing, this can be done via pip with  
```> pip install matplotlib pyserial typing```
3. Try running it... There may be other dependencies depending on your system that weren’t installed automatically.  If it crashes due to missing imports, the error message should include the name of the missing library which can be installed via pip.  If you run into any of these please tell me (Lucas)

### Method 3 - setup with manual installation of libraries
You shouldn't really ever need to do this anymore, unless you are having trouble with the virtual env.  

#### Linux
1. Install python3 and python3-pip via apt-get
2. Install matplotlib, pyserial and typing via pip3
3. Try running it... There may be other dependencies depending on your system that weren’t installed automatically.  If it crashes due to missing imports, the error message should include the name of the missing library which can be installed via pip3.  If you run into any of these please tell me (Lucas)

#### Mac
Same as instructions for Linux, except you will likely need to install a package manager first instead of apt-get (I have found that brew works well)

## Building a distribution
If you want to create a packaged dist that others can use without installing python and the needed libraries, you can do this with the included makefile.  It uses pyinstaller to bundle the source code, all needed libraries and the python interpreter into one binary.  If you are running on Linux, wine is used to cross-compile executables for Windows.  The reverse should also be possible eventually once the Linux subsystem for Windows is released.  

1. Make sure that you can run the code directly and that all needed libraries are installed, as above.  
2. Run ```make``` with no arguments (you can add the -j4 flag to build in parallel, if your system supports it.)  The resulting binaries will go in the 'dist' folder.
On Windows you may run into errors with something called 'pefile' missing.  If so, you can install that library via pip.
If things crash after building more than once, you can delete the generated build folder.  
You should just be able to run on Linux to make a Linux dist, and on Windows to make a Windows dist.  

### Setting up a WINE virtual env with python
Shouldn't need to do this again, but I am including this here for reference.  

1. Install wine (can be done via apt-get on Linux or brew on a Mac)
2. Clone the repository 'virtual-wine': https://github.com/htgoebel/virtual-wine.git
3. Run the vwine setup script with the location of the new wine virtual env
```> virtual-wine/vwine-setup wine_venv```
4. Activate the virtual env for the current session
```
> cd wine_venv
> source bin/activate
```
5. Get a msi python installer image for a recent release of python 3.4+.  As of writing, the latest is 3.4.4:  
```> wget https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi```
6. Install python onto the wine virtual windows environment:  
```> wine msiexec /i python-3.4.4.msi```
This will open a grapical Windows installer window, you should be able to click through this keeping the default options.  This will install both python 3 and pip.
7. Copy the executables python.exe and pip*.exe from ```~/.wine/drive_c/Python34``` to ```~/.wine/drive_c/windows```.  This makes it so you don't have to give the absolute paths to the exes to wine every time you want to run.
8. Verify that python is working correctly by running  
```> wine python```
This should print the python version and start the python REPL.
9. Install pefile (both needed for pyinstaller on Windows), matplotlib, pyserial, and typing, this can be done via pip with  
```> wine python -m pip install -U pefile matplotlib pyserial typing```
10. Install pywin32, the excutable installer can be downloaded from https://sourceforge.net/projects/pywin32/ and run with wine
```> wine ../pyToExe/pywin32-220.win32-py3.4.exe```
11. Check that everything is working correctly, run the command
```> wine python -c 'import matplotlib; import serial; import typing; import pywintypes'```
The exit code should be 0.  

## Repository Layout
* include/Telemetry - Contains Telemetry.h file detailing communication conventions for the Arduino. Must change paramater to switch communication modes between Serial, Ethernet TCP, Ethernet UDP, etc. 
* libs - Contains Telemetry.zip of Telemetry.h file for easy distribution to Arduino. 
* build_tools - A link to another repository of the same name. Contains tools to distribute the GUI, to run it on multiple platforms. 
* dist - Contains built executables of the GUI, one for both Windows/*nix systems. Includes various configurations, such as mk1/2_static_test, pressure_test, flight, demo_static_test, etc. 
* drivers - Contains Python3 scripts specifying the design of each GUI to be built in dist/ directory. The demo, mk1, and mk2 scripts are wrappers around static_test_gui.py, the main script. 
* src - Contains Python3 scripts handling the components of the GUI and the GUI class. Includes plotting, managing, and IO (serial, ethernet, etc) classes. 

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
