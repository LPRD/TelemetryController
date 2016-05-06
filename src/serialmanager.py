import serial
import sys
import glob
import time

# Manages recieving data from a serial port and passes it to a Dispatcher
class SerialManager:
    def __init__(self, dispatcher, port='/dev/ttyACM0', baud=9600):
        self.dispatcher = dispatcher
        self.baud = baud
        if sys.platform.startswith('win'):
            self.ser = serial.Serial("\\.\COMxx" + port, baud)
        else:
            self.ser = serial.Serial(port, baud)
        
        self.paused = False

        self.dispatcher.reset()

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
            if sys.platform.startswith('win'):
                s = serial.Serial("\\.\COMxx" + port)
            else:
                s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
