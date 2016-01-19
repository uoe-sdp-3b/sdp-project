#!/usr/bin/env python
from communication.communications import RobotComms
from ncurses.cursesUI import NcursesUI

class Console():
  def __init__(self, port):
    self.robot = RobotComms(port)
    self.ui = NcursesUI(self.read, self.write)

  def start():
    robot.connect()
    ui.start()

  def read():
    return "Hello"

  def write(message):
    pass

def main():
  console = Console("/dev/ttyACM0")
  console.start()


if __name__ == "__main__":
  main()
