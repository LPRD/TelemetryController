import sys
import socket
import select
from typing import *
from manager import Dispatcher, Writeable

class SocketManager:
    """Manages recieving data from a serial port and passes it to a Dispatcher."""
    
    paused = False

    def __init__(self, dispatcher: Dispatcher, socket: socket) -> None:
        self.dispatcher = dispatcher
        self.socket = socket

        self.dispatcher.reset()

    def __del__(self):
        self.socket.close()

    def handleInput(self,
                txtout: Writeable = sys.stdout,
                errout: Writeable = sys.stderr):
        """Check if data is available, and if so send it to the dispatcher or
        appropriate output stream."""

        # Check if data is available in socket
        readable, _, _ = select.select([self.socket], [], [], 0)

        if readable and not self.paused:
            # Read from socket
            bytes_in = self.socket.recv(1024)
            if not bytes_in:
                raise BrokenPipeError("Socket closed")

            decode = bytes_in.decode("utf-8", errors='ignore')
            self.dispatcher.acceptText(decode, txtout, errout)
            return True
        return False
    
    def write(self, txt: Text):
        """Send the given text back out the serial port."""
        if not self.socket.send(txt.encode()):
            raise BrokenPipeError("Socket closed")



def makeManager(dispatcher: Dispatcher):
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the server
    # IP=beaglebone.local
    # Port=5000
    try:
        client_socket.connect(('beaglebone.local', 5000))
    except socket.gaierror as e:
        print(f"Beaglebone not found: {e.strerror}")
        return None
    except ConnectionRefusedError as e:
        print(f"Beaglebone refused to connect: {e.strerror}")
        return None
    
    return SocketManager(dispatcher, client_socket)
