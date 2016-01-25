import serial

class SerialReader:
    def __init__(self, manager, port='/dev/ttyACM0', baud=9600):
        self.manager = manager
        self.ser = serial.Serial(port, baud)
        
    def start(self):
        self.manager.start()
        while True:
            data = self.ser.readline().decode("utf-8")
            if data.startswith("@@@@@"):
                data = data[5:]
                name, value = data.split(':')
                self.manager.accept(name, value)
