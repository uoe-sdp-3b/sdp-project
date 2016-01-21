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
    
    seqNo = False
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

    def _write(self, sig, opcode, arg, seqNo):
        """
        Repeatedly sends the opcode to the robot until an OK is received.
        Then waits until DONE, and sets "ready" true.
        """

        received = None
        checksum = self.create_checksum(arg, opcode)

        # If message start with robotGrab
        # The robot executed the action
        while received[:5] != "Robot":
          opcode_string = "%d%d%03d%d%d\r" % (sig, opcode, arg, checksum, seqNo)
          self.comn.write(opcode_string)
          sleep(0.2) # Possibly unnecessary
          received = self.comn.readline()
          
          # Checksum failure
          if received == "Checksum failed\r\n":
            print "Checksum Failed", opcode_string
            seqNo = not seqNo
          
          # Command did not get recognized
          if received == "Wat?\r\n":
            print "WAT WAT? Arduino did not understand its input", opcode_string
        
        # Print robot executed action
        print received
        print
        self.ready = True

    def write(self, sig, opcode, arg):
        """
        Public interface for sending opcodes to the robot
        """

        if self.isConnected:
            self.ready = False
            self.seqNo = not self.seqNo
            
            thread = Thread(target = self._write, args = (sig, opcode, arg, self.seqNo))
            thread.start()
        else:
            print("Not connected to Arduino.")

# plan on keeping this as a skeleton used purely for communication
class RobotComms(CommsToArduino):
  def __init__(self, port):
    super(RobotComms, self).__init__(port)

  def stop(self):
    #self.write(sig, opcode, arg)
    #011001
    #print "forward: " + speed
    self.write(0, 0, 0)

  def forward(self, speed):
    #self.write(sig, opcode, arg)
    #011001
    #print "forward: " + speed
    self.write(0, 1, speed)

  def backward(self, speed):
    #self.write(sig, opcode, arg)
    self.write(0, 2, speed)

  def left(self, speed):
    #self.write(sig, opcode, arg)
    self.write(0, 3, speed)

  def right(self, speed):
    #self.write(sig, opcode, arg)
    self.write(0, 4, speed)

  def grab(self, speed):
    #self.write(sig, opcode, arg)
    self.write(0, 5, speed)

if __name__ == "__main__":
  print("This class is not designed to be run by hand")
