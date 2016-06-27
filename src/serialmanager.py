import serial
import sys
import glob
import time

# Manages recieving data from a serial port and passes it to a Dispatcher
class SerialManager:
    ports = {}
    def __init__(self, dispatcher, port='/dev/ttyACM0', baud=9600):
        self.dispatcher = dispatcher
        self.baud = baud
        
        # Prevent opening a port more than once on windows
        try:
            self.ser = serial.Serial(port, baud)
            SerialManager.ports[port] = self.ser
        except (OSError, serial.SerialException) as e:
            if port in SerialManager.ports:
                self.ser = SerialManager.ports[port]
            else:
                raise e
        
        self.paused = False

        self.dispatcher.reset()

    def __del__(self):
        self.ser.close()

    def handleInput(self, txtout=sys.stdout, errout=sys.stderr):
        while self.paused:
            time.sleep(100 / 1000) # Sleep 100 ms
        if self.ser.in_waiting:
            try:
                bytes_in = self.ser.read(self.ser.in_waiting)
            except serial.serialutil.SerialException:
                time.sleep(10 / 1000) # Sleep 10 ms
            decode = bytes_in.decode("utf-8", errors='ignore')
            self.dispatcher.acceptText(decode, txtout, errout)
            return True
        return False
    
    def write(self, txt):
        self.ser.write(txt.encode())
        self.ser.flush()

# Utility function, get the list of all available serial devices
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
#        # Check if running on WINE
#        import winreg
#        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
#        try:
#            k = winreg.OpenKey(reg, "SOFTWARE\Wine")
#            # Regestry opened, so we are on WINE
#            ports = glob.glob('/dev/tty[A-Za-z]*')
#        except:
#            # On Windows
#            ports = ['COM%s' % (i + 1) for i in range(256)]
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            if port in SerialManager.ports and SerialManager.ports[port].isOpen():
                result.append(port)
    return result
