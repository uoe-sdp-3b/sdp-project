#!/usr/bin/env python
from serial import Serial
from Queue import Queue
import fileinput
import readline
from time import sleep
from threading import Thread
from random import randint


# constants
TEAM = 0

# Operation Codes (OpCodes)
STOP = 0
FORWARD = 1
BACKWARD = 2
LEFT = 3
RIGHT = 4
KICK = 5
GRAB = 6
STORE = 7


class CommsToArduino(object):

    queue = Queue()
    internal_queue = Queue()
    write_queue = Queue()
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
        Sends the code to the Arduino
        """
        checksum = self.create_checksum(arg, opcode)
        opcode_string = "%d%d%03d%d%d\r" % (sig, opcode, arg, checksum, seqNo)
        self.to_robot(opcode_string)
        return

    def to_robot(self, message):
        self.comn.write(message)

    def write(self, sig, opcode, arg):
        """
        Public interface for sending opcodes to the robot
        """

        if self.isConnected:
            self.ready = False
            self.seqNo = not self.seqNo

            self.write_queue.put({
                'sig': sig,
                'opcode': opcode,
                'arg': arg,
                'seqNo': self.seqNo
            })
        else:
            print("Not connected to Arduino.")

# plan on keeping this as a skeleton used purely for communication
class RobotComms(CommsToArduino):
  _close = False

  def __init__(self, port):
      self.write_thread = Thread(target = self.write_stream)
      self.read_thread = Thread(target = self.read_stream)
      self.read_thread.start()
      self.write_thread.start()
      super(RobotComms, self).__init__(port)

  def close(self):
      self._close = True
      self.comn.close()
      self.queue.put("Robot Closed")


  def write_stream(self):
      while True:
          if self._close:
              self.queue.put("Read Stream Closed")
              break
          if not self.write_queue.empty():
              msg_dict = self.write_queue.get()
              self._write(
                  msg_dict["sig"],
                  msg_dict["opcode"],
                  msg_dict["arg"],
                  msg_dict["seqNo"]
              )

  def read_stream(self):
      while True:
          if self._close:
              self.queue.put("Read Stream Closed")
              break
          sleep(0.5)
          if self.comn and self.comn.is_open:
              line = self.comn.readline()
              if line.strip() != "":
                  self.queue.put(line)

  def stop(self):
      self.write(TEAM, STOP, 0)

  def forward(self, speed):
      self.write(TEAM, FORWARD, int(speed))

  def backward(self, speed):
      self.write(TEAM, BACKWARD, int(speed))

  def left(self, speed):
      self.write(TEAM, LEFT, int(speed))

  def right(self, speed):
      self.write(TEAM, RIGHT, int(speed))

  def kick(self, speed):
      self.write(TEAM, KICK, speed)

  def grab(self, speed):
      self.write(TEAM, GRAB, speed)
  
  def store(self, file_path, frequency):
      with open(file_path,'r') as f:
          file_contents = f.read()
          bytes_to_store = len(file_contents)
          # Randint is a hack, but this is only going to be used for 2 tests
          checksum = self.create_checksum(bytes_to_store, STORE)
          init_command = "%d%d%03d%d%d\r" % (TEAM, STORE, bytes_to_store, checksum, randint(2,1000000))
          self.to_robot(init_command)
          sleep(1)
          for byte in file_contents:
              self.to_robot(byte)
              sleep(1/float(frequency)) # can be changed

if __name__ == "__main__":
    print("This class is not designed to be run by hand")
