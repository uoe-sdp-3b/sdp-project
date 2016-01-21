#!/usr/bin/env python
from communication.communications import RobotComms
from ncurses.cursesUI import NcursesUI

class Console():
  def __init__(self, port):
    self.robot = RobotComms(port)
    self.ui = NcursesUI(self.read, self.write)

  def start(self):
    self.robot.connect()
    self.ui.start()

  def read(self):
    x = self.robot.comn.readline()
    if x.strip() is "":
      return None
    return x

  def write(self, message):
    args = message.split(" ")
    f = getattr(self.robot, args[0], None)

    if f and len(args) > 1:
      f(*args[1:])

def main():
  console = Console("/dev/ttyACM0")
  console.start()


if __name__ == "__main__":
  main()
