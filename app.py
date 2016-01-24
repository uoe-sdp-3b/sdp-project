#!/usr/bin/env python2.7
from communication.communications import RobotComms

# parse args
def main():
  comms = RobotComms("/dev/ttyACM0")
  comms.connect()

if __name__ == "__main__":
  main()
