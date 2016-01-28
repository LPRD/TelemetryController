import serial
import sys
import glob
import multiprocessing
import time

def serialIO(ser, queue):
    while True:
        try:
            queue.put(ser.readline().decode("utf-8").rstrip())
            time.sleep(1 / 1000)
        except serial.serialutil.SerialException: # This error causes random crashes, appairently a kernal bug
            print("Serial error!!!")
            time.sleep(10 / 1000)
            pass 

class SerialManager:
    def __init__(self, manager, port='/dev/ttyACM0', baud=115200):
        self.manager = manager
        self.ser = serial.Serial(port, baud)
        self.running = False
        
    def start(self, txtout=sys.stdout):
        self.queue = multiprocessing.Queue()
        self.proc = multiprocessing.Process(target=serialIO, args=(self.ser, self.queue))
        self.proc.start()
        self.running = True
        
    def stop(self):
        self.proc.terminate()
        self.running = False

    def handleInput(self, txtout=sys.stdout):
        if not self.running:
            self.start(txtout)
        while not self.queue.empty():
            line = self.queue.get()
            if self.manager.running:
                if line.startswith("@@@@@"):
                    try:
                        time, name, value = line[5:].split(':')
                        self.manager.accept(name, int(time), value)
                    except ValueError:
                        print("Ill-formed data packet", line)
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
