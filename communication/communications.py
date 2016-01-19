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
                
    def create_checksum(self, args):
        """
        Creates the checksum that is used to verify the command.
        """
        
        sum = 0
        for arg in args:
            sum += abs(arg)
        return sum % 10

    def _write(self, command, seqNo, args):
        """
        Repeatedly sends the command to the robot until an OK is received.
        Then waits until DONE, and sets "ready" true.
        """

        received = None

        string_args = ' '.join(['%d' % x for x in args])
        checksum = self.create_checksum(args)

        while received != "DONE\r\n":
          command_string = "%s %d %s %d\r" % (command, seqNo, string_args, checksum)
          self.comn.write(command_string)
          sleep(0.2)
          received = self.comn.readline()
          
          if received == "Checksum failed\r\n":
            print "Checksum Failed", command_string
            seqNo = not seqNo

          if received == "Wat?\r\n":
            print "WAT WAT?", command_string

        print "  DONE"
        print
        self.ready = True

    def write(self, command, args):
        """
        Public interface for sending commands to the robot
        """

        if self.isConnected:
            self.ready = False
            self.seqNo = not self.seqNo

            thread = Thread(target = self._write, args = (command, self.seqNo, args))
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
