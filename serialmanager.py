import serial
import sys
import glob

class SerialManager:
    def __init__(self, manager, port='/dev/ttyACM0', baud=9600):
        self.manager = manager
        self.ser = serial.Serial(port, baud)
        
    def start(self, txtout=sys.stdout):
        self.manager.start()
        while True:
            line = self.ser.readline().decode("utf-8").rstrip()
            if line.startswith("@@@@@"):
                line = line[5:]
                name, value = line.split(':')
                self.manager.accept(name, value)
            else:
                print(line, file=txtout)

    def tryInput(self, txtout=sys.stdout):
        if self.ser.inWaiting():
            line = self.ser.readline().decode("utf-8").rstrip()
            if self.manager.isrunning():
                if line.startswith("@@@@@"):
                    try:
                        name, value = line[5:].split(':')
                    except ValueError:
                        print("Ill-formed data packet", line)
                    else:
                        self.manager.accept(name, value)
                else:
                    print(line, file=txtout)
    
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
