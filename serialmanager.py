import serial
import sys

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
