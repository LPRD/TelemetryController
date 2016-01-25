import serial

class SerialReader:
    def __init__(self, manager, port='/dev/ttyACM0', baud=9600):
        self.manager = manager
        self.ser = serial.Serial(port, baud)
        
    def start(self):
        self.manager.start()
        while True:
            line = self.ser.readline().decode("utf-8").rstrip()
            if line.startswith("@@@@@"):
                line = line[5:]
                name, value = line.split(':')
                self.manager.accept(name, value)
            else:
                print(line)
