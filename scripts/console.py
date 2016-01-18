#!/usr/bin/env python
from serial import Serial
import fileinput
import readline
import time

# this file literally wraps some convenience things in functions


def constructConsole():
  console = Serial(port="/dev/ttyACM1", timeout=0)
  return console

def main():
  console = constructConsole()
  print("Write commands here:")
  while True:
    input = raw_input()
    console.write(input)
    time.sleep(0.2)
    print(console.readline())

if __name__ == "__main__":
  main()
