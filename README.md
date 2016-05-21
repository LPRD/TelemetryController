# Telemetry-display
Python matplotlib-based graphical viewer for telemetry streams

## Setup instructions
### Method 1 - run-only, no development
Do this if you only want to run the program and won't need to make any changes to the source.  
You can simply download the packaged executables under dist, which should run with no extra dependencies.  Use the .exe binaries on Windows, or the binaries with no extension on Mac and Linux

### Method 2 - setup for development
#### Linux and Mac
**There is now no need to install python or any libraries!**  Everything is included in the virtual python env.  To use it,
simply run  
```> source build_tools/linux_venv/bin/activate```  
from your shell.  This will load the enclosed instance of python along with the needed libraries.  Then you can simply run the gui scripts directly  
```> src/static_test_gui```  
Note that any python libraries installed via pip with the virtual env activated will be installed to the virtual env.  

#### Windows
Jon is working on setting up libraries to do development on Windows and will update this when he is done.  The libraries should be the same as for Linux.  

### Method 3 - setup with manual installation of libraries
You shouldn't really ever need to do this anymore, unless you are having trouble with the virtual env.  

#### Linux
1. Install python3 and python3-pip via apt-get
2. Install matplotlib and pyserial via pip3
3. Try running it... There may be other dependencies depending on your system that weren’t installed automatically.  If it crashes due to missing imports, the error message should include the name of the missing library which can be installed via pip3.  If you run into any of these please tell me (Lucas)

#### Mac
Same as instructions for Windows, except you will likely need to install a package manager first instead of apt-get (I have found that brew works well)

## Building a distribution
If you want to create a packaged dist that others can use without installing python and the needed libraries, you can do this with the make_dist script.  It uses pyinstaller to bundle the source code, all needed libraries and the python interpreter into one binary.  

### Building on the target system with native python
1. Make sure that you can run the code directly and that all needed libraries are installed, as above.  
2. Run the ```make_dist``` script with no arguments.  The resulting binaries will go in the 'dist' folder.
On Windows you may run into errors with something called 'pefile' missing.  If so, you can install that library via pip.
If things crash after building more than once, you can delete the generated build folder.  
You should just be able to run on Linux to make a Linux dist, and on Windows to make a Windows dist once bash for Windows is released.
Note that Linux dist builds with native python may be very large due to extra libraries being included, you may want to build with the virtual python env as below:

### Building on Mac/Linux with virtual python
Same as above, but include the --virtual-linux-build flag.  This will load the virtual python env and use that instead of your native installation.  

### Cross-compiling a Windows distribution using WINE on Mac/Linux
Unless you have a Linux/Mac computer and *really* want to build a Windows exe, you should ignore this.  I am putting it here for reference anyway.  

1. Install wine (can be done via apt-get on Linux or brew on a Mac)
2. Get a msi python installer image for a recent release of python 3.4+.  As of writing, the latest is 3.4.4:  
```> wget https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi```
3. Install python onto the wine virtual windows environment:  
```> wine msiexec /i python-3.4.4.msi```  
This will open a grapical Windows installer window, you should be able to click through this keeping the default options.  This will install both python 3 and pip.
4. Copy the executables python.exe and pip*.exe from ```~/.wine/drive_c/Python34``` to ```~/.wine/drive_c/windows```.  This makes it so you don't have to give the absolute paths to the exes to wine every time you want to run.
5. Verify that python is working correctly by running  
```> wine python```
This should print the python version and start the python REPL.
6. Install pefile (needed for pyinstaller on Windows), matplotlib and pyserial, this can be done via pip with  
```> wine python -m pip install -U pefile matplotlib pyserial```
7. You are finally ready to build!  Run  
```> ./make_dist --wine-build```.  
This should build the executatbles and put them in the dist folder.
8. To test the build, you can run the exes with wine:  
```> wine dist/flight_test_gui.exe```
9. Remember to commit and push the new builds to be public on github, if you are ready.  

## TODO items
### Major
* Get CSV parsing working  

### Minor
* Nice setup configuration modes (What did I mean by this?)

## Known issues
* No automatic restart after port change, need to start/stop/reset (check if resolved?)
