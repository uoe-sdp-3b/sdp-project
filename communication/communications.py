#!/usr/bin/env python
from serial import Serial
import fileinput
import readline
from time import sleep
from threading import Thread

class CommsToArduino(object):
    # these should be hard-coded, the values should not change
    def __init__(self, port="/dev/ttyACM0",
                 rate=115200,
                 timeout=0,
                 connected=False):
        self.isConnected = connected
        self.port = port
        self.comn = None # updated when we establish the connection
        self.rate = rate
        self.timeout = timeout
        self.connect()

    ready = True

    # this function establishes the connection between the devices
    # and updates the boolean variable isConnected
    def connect(self):
        if self.isConnected is False and self.comn is None:
            try:
                self.comn = Serial(port=self.port,
                                   baudrate=self.rate,
                                   timeout=self.timeout)
                self.isConnected = True
            except OSError as ex:
                print("Cannot connect to Arduino.")
                print(ex.strerror)
                
    def create_checksum(self, arg, opcode):
        """
        Creates the checksum that is used to verify the opcode.
        """
        
        return (arg + opcode) % 10

    def _write(self, sig, opcode, arg):
        """
        Repeatedly sends the opcode to the robot until an OK is received.
        Then waits until DONE, and sets "ready" true.
        """

        received = None
        checksum = self.create_checksum(arg, opcode)

        while received != "DONE\r\n":
          opcode_string = "%d%d%d%d\r" % (sig, opcode, arg, checksum)
          self.comn.write(opcode_string)
          sleep(0.2)
          received = self.comn.readline()
          
          # Checksum failure
          if received == "Checksum failed\r\n":
            print "Checksum Failed", opcode_string
          
          # Command did not get recognized
          if received == "Wat?\r\n":
            print "WAT WAT?", opcode_string

        print "  DONE"
        print
        self.ready = True

    def write(self, opcode, arg):
        """
        Public interface for sending opcodes to the robot
        """

        if self.isConnected:
            self.ready = False

            thread = Thread(target = self._write, args = (sig, opcode, arg))
            thread.start()
        else:
            print("Not connected to Arduino.")

# plan on keeping this as a skeleton used purely for communication
class RobotComms(CommsToArduino):
  def __init__(self, port):
    super(RobotComms, self).__init__(port)

  def forward(self, speed):
    print "forward: " + speed

  def backward(self, speed):
    pass

  def left(self, speed):
    pass

  def right(self, speed):
    pass

  def grab(self):
    pass

if __name__ == "__main__":
  print("This class is not designed to be run by hand")
