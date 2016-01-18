#!/usr/bin/env python2.7
from communication.communications import CommsToArduino

# tmp imports
import time


# parse args
def main():
  comms = CommsToArduino()
  comms.connect()

  while True:
    input = raw_input()
    comms.write(input, "")

if __name__ == "__main__":
  main()
