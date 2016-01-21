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
    if not self.robot.queue.empty():
      message = self.robot.queue.get()
      return message.strip()
    return None

  def write(self, message):
    args = message.split(" ")
    f = getattr(self.robot, args[0], None)

    if f and len(args) > 1:
      f(*args[1:])
    elif f:
      f()

def main():
  import argparse
  parser = argparse.ArgumentParser(description="console for robot")
  parser.add_argument("-p", default="/dev/ttyACM0")

  args = parser.parse_args()

  console = Console(args.p)
  console.start()


if __name__ == "__main__":
  main()
