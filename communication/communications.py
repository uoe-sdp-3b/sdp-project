#!/usr/bin/env python
from serial import Serial
from Queue import Queue
from time import sleep
from threading import Thread
from random import randint
from math import *
import sys

import time as time_

# from vision.G3VisionAPI import *


# constants
TEAM = 0

# Operation Codes (OpCodes)
STOP = 0
FORWARD = 1
BACKWARD = 2
LEFT = 3
RIGHT = 4
KICK = 5
# GRAB = 6
# STORE = 7
OPEN_GRABBER = 6
CLOSE_GRABBER = 7

READ_COMPASS = 8
READ_INFRARED = 9
READ_SONAR = 10
SCALE_LEFT = 11
SCALE_RIGHT = 12

PING = 14
GET_INFO = 15
FORWARD_SLOW = 16

# length to grabber from centre of robot
LENGTHBUFFER = 12


class CommsToArduino(object):

    queue = Queue()
    internal_queue = Queue()
    write_queue = Queue()

    ready = True
    seqNo = 0

    # these should be hard-coded, the values should not change
    def __init__(self, port="/dev/ttyACM0", rate=115200, timeout=0, connected=False):
        self.isConnected = connected
        self.port = port
        self.comn = None  # updated when we establish the connection
        self.rate = rate
        self.timeout = timeout
        self.connect()

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


    def millis(self, start_time):
        st = int(round(start_time * 1000))
        ms = int(round(time_.time() * 1000))
        return ms-st


    def _write(self, sig, opcode, arg):
        """
        Sends the code to the Arduino
        """
        checksum = self.create_checksum(arg, opcode)    
        opcode_string = "%02d%03d%d%d\r" % (opcode, arg, checksum, self.seqNo)
        # Ensure that internal queue is clear initially
        self.internal_queue.queue.clear()
        # Send command
        self.to_robot(opcode_string)


        # 1. send command wait for response
        # if time passed 200 milliseconds resend command
        # only exit loop once acknowledgement is accepted that the first command have been recieved and is being processed
        sent_successfully = False
        start_time_1 = time_.time()
        timeout = 200 # 200 milliseconds, might want to increase!


        # initialize values for response sequence number, done and corruption bits
        corr = ""
        done = ""
        rseqNo = 0

        while(not sent_successfully):
            sleep(0.25)
            # check response queue is not empty
            # if it is loop until it is not
            if not self.internal_queue.empty():
                response = self.internal_queue.get()

                # check response is not an unregonized command (if so just return)
                # this in theory should never happen
                if (response == "0001"):
                    return

                if(len(response) >= 3):
                    corr = response[0]
                    done = response[2]

                    if(response[1] == "1"):
                        rseqNo = 1

                # get time in milliseconds since the command was sent
                # if this value is greater than 200 resend the command
                if(corr == "0" and self.seqNo == rseqNo and done == "1"):
                    sent_successfully = True
                    if(self.seqNo == 0):
                        self.seqNo = 1
                    else:
                        self.seqNo = 0
                    # start_time_2 = time_.time() # begin 2nd timer for 2nd acknowledgement
                else:
                # check if 200 milliseconds has passed since the last time the command was sent
                    self.to_robot(opcode_string)
                    # start_time_1 = time_.time_ime()

            # else:
            #     # check if 200 milliseconds has passed since the last time the command was sent
            #     x = self.millis(start_time_1)
            #     if(x > timeout):
            #         self.to_robot(opcode_string)
            #         start_time_1 = time_.time()

        return


        # 2. now we need to wait for the 2nd acknowledgement to state that the command has been executed
        # completed_instruction = False

        # while(not completed_instruction):
        #     if not self.internal_queue.empty():
        #         response = self.internal_queue.get()

        #         # this should never happen!
        #         # if (response == "0001"):
        #         #     return

        #         if(len(response) >= 3):
        #             corr = response[0]
        #             done = response[2]

        #             if(response[1] == "1"):
        #                 rseqNo = 1

        #         if(corr == "0" and self.seqNo == rseqNo and done == "1"):
        #             if(self.seqNo == 0):
        #                 self.seqNo = 1
        #             else:
        #                 self.seqNo = 0
                    
        #             return

        #     # queue is empty
        #     # check for timeout, if timeout send command asking for it to resend 2nd acknowledgement
        #     # this command itself does not need an acknolwdgement message back!
        #         else:
        #             x = self.millis(start_time_2)
        #             # checks if time since 1st acknowledgement been received and NOW has passed 500 millisconds
        #             # if so resends command to ask for 2nd acknowledgement again
        #             if(x >= 4000):
        #                 opcode_string2 = "%02d%03d%d%d\r" % (17, 0, 7, self.seqNo)
        #                 self.to_robot(opcode_string2)
        #                 start_time_2 = time_.time()




        # while (not completed_instruction):
        #     sleep(0.25)
        #     if not self.internal_queue.empty():
        #         response = self.internal_queue.get()

        #         # Check if success
        #         # (not checksum fail or unrecognized or bad command length)
        #         # Note: would be better to have a specific response upon success
        #         corr = ""
        #         done = ""
        #         rseqNo = 0

        #         if(response == "0001"):
        #             #unregonized command (this should not happen)
        #             return

        #         if(len(response) >= 3):
        #             corr = response[0]
        #             done = response[2]

        #             if(response[1] == "1"):
        #                 rseqNo = 1

        #         if(not sent_successfully):

        #             if(corr == "0" and self.seqNo == rseqNo and done == "0"):
        #                 sent_successfully = True
        #                 # start timer
        #                 start_time_2 = datetime.now()

        #             else:  
        #                 self.to_robot(opcode_string)

        #         else:

        #             # if timeout ask for 2nd acknowledgement
        #             # this should resend the 2nd last acknowledgement as per the arduino code (double check)
        #             # what about if first instructions is still in execution?
        #             x = millis(start_time_2)
        #             if(x >= timeout):
        #                 opcode_string2 = "%02d%03d%d%d\r" % (17, 0, 7, self.seqNo)
        #                 self.to_robot(opcode_string2)

        #             if(corr == "0" and self.seqNo == rseqNo and done == "1"):
        #                 completed_instruction = True
        #                 if(self.seqNo == 0):
        #                     self.seqNo = 1
        #                 else:
        #                     self.seqNo = 0

        # return

    def to_robot(self, message):
        # Send command
        self.comn.write(message)

    def write(self, sig, opcode, arg):
        """
        Public interface for sending opcodes to the robot
        """

        if self.isConnected:
            self.ready = False

            self.write_queue.put({
                'sig': sig,
                'opcode': opcode,
                'arg': arg,
            })
        else:
            print("Not connected to Arduino.")


# plan on keeping this as a skeleton used purely for communication
class RobotComms(CommsToArduino):
    _close = False
    # last value read from the read_stream
    internal_queue = Queue()

    # the message to wait for, or None if we aren't to wait
    wait_msg = None

    def __init__(self, port):
        self.write_thread = Thread(target=self.write_stream)
        self.read_thread = Thread(target=self.read_stream)
        self.read_thread.start()
        self.write_thread.start()
        super(RobotComms, self).__init__(port)

    def g(self):
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
                self._write(msg_dict["sig"], msg_dict["opcode"],
                            msg_dict["arg"])

    def read_stream(self):
        while True:
            if self._close:
                self.queue.put("Read Stream Closed")
                break
            # Sleep needed to not just put single letters into queue
            sleep(0.2)
            if self.comn and self.comn.is_open:
                line = self.comn.readline().strip()
                if line != "":
                    self.queue.put(line)
                    self.internal_queue.put(line)

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
        self.write(TEAM, KICK, int(speed))

    def grab(self, speed):
        self.write(TEAM, GRAB, int(speed))

    def store(self, file_path, frequency):
        with open(file_path, 'rb') as f:
            file_contents = f.read()
            bytes_to_store = len(file_contents)
            # Randint is a hack, but this is only going to be used for 2 tests
            checksum = self.create_checksum(bytes_to_store, STORE)
            init_command = "%d%d%03d%d%d\r" % (TEAM, STORE, bytes_to_store,
                                               checksum, randint(2, 1000000))
            self.to_robot(init_command)
            sleep(1)
            for byte in file_contents:
                self.to_robot(byte)
                sleep(1 / float(frequency))  # can be changed


    def open_grabber(self):
        self.write(TEAM, OPEN_GRABBER, 80)

    def close_grabber(self):
        self.write(TEAM, CLOSE_GRABBER, 80)


    def read_compass(self):
        self.write(TEAM, READ_COMPASS, 0)

    def read_infrared(self):
        self.write(TEAM, READ_INFRARED, 0)

    def read_sonar(self):
        self.write(TEAM, READ_SONAR, 0)

    def scale_left(self, scale):
        self.write(TEAM, SCALE_LEFT, int(scale))

    def scale_right(self, scale):
        self.write(TEAM, SCALE_RIGHT, int(scale))

    def ping(self):
        self.write(TEAM, PING, 0)

    def testcomms(self):
        for x in range(0,400):
            self.write(TEAM,PING,0)

    def getinfo(self):
        self.write(TEAM, GET_INFO, 0)

    def forwardSlow(self, distance):
        self.write(TEAM, FORWARD_SLOW, distnace)


    def c(self, *args):
        self.compose(args)

    # compose commands together with a '$' separator
    def compose(self, *args):
        my_args = " ".join(args).split("$")
        for command in my_args:
            args_local = command.strip().split(" ")
            f = getattr(self, args_local[0], None)
            try:
                if f and len(args_local) > 1:
                    f(*args_local[1:])
                elif f:
                    f()
                else:
                    self.queue.put("argument: '%s' doesn't exist" %
                                   args_local[0])
            except TypeError as e:
                self.queue.put(str(e))



if __name__ == "__main__":
    print("This class is not designed to be run by hand")
