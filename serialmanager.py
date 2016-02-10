import serial
import sys
import glob
import time

class SerialManager:
    def __init__(self, dispatcher, port='/dev/ttyACM0', baud=9600):
        self.dispatcher = dispatcher
        self.baud = baud
        self.ser = serial.Serial(port, baud)
        self.current_line = ""

    def handleInput(self, txtout=sys.stdout):
        if self.ser.in_waiting:
            try:
                bytes_in = self.ser.read(self.ser.in_waiting)
            except serial.serialutil.SerialException:
                time.sleep(10 / 1000)
            decode = bytes_in.decode("utf-8")
            lines = (decode + self.current_line).split("\r\n")
            for line in lines[:-1]:
                if line.startswith("@@@@@") and line.endswith("&&&&&"):
                    try:
                        time, name, value = line[5:][:-5].split(':')
                        self.dispatcher.accept(name, int(time) if time else None, value)
                    except ValueError:
                        print("Ill-formed data packet", line)
                else:
                    print(line, file=txtout)
            if lines[-1].startswith("@"):
                self.current_line = lines[-1]
            else:
                print(lines[-1], end='', file=txtout)
                self.current_line = ""
            return True
        return False
    
    def write(self, txt):
        self.ser.write(txt.encode())
        self.ser.flush()

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
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
