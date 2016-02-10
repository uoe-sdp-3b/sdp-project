#!/usr/bin/env python
from serial import Serial
from Queue import Queue
from time import sleep
from threading import Thread
from random import randint
from math import *
from vision.camera import Camera

import sys
from vision.G3VisionAPI import *


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
OPEN = 8
CLOSE = 9

# length to grabber from centre of robot
LENGTHBUFFER = 12

ERROR_CODES = ["0CF","0UC", "0IW"]

RETURN_CODE = {
    "STOP": "0RS",
    "FORWARD": "0RF",
    "BACKWARD": "0RB",
    "LEFT": "0RL",
    "RIGHT": "0RR",
    "KICK": "0RK",
    "GRAB": "0RG",
    "OPEN": "0RO",
    "CLOSE": "0RC"
}


class CommsToArduino(object):

    queue = Queue()
    internal_queue = Queue()
    write_queue = Queue()

    # these should be hard-coded, the values should not change
    def __init__(self,
                 port="/dev/ttyACM0",
                 rate=115200,
                 timeout=0,
                 connected=False):
        self.isConnected = connected
        self.port = port
        self.comn = None  # updated when we establish the connection
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

    def _write(self, sig, opcode, arg):
        """
        Sends the code to the Arduino
        """
        checksum = self.create_checksum(arg, opcode)
        self.seqNo = not self.seqNo
        opcode_string = "%d%d%03d%d%d\r" % (sig, opcode, arg, checksum, self.seqNo)
        # Ensure that internal queue is clear initially
        self.internal_queue.queue.clear()
        # Send command
        self.to_robot(opcode_string)

        # Keep sending command every 0.25s until you get a received OK response
        sent_successfully = False
        while (not sent_successfully):
            sleep(0.25)
            if not self.internal_queue.empty():
                response = self.internal_queue.get()

                # Check if success
                # (not checksum fail or unrecognized or bad command length)
                # Note: would be better to have a specific response upon success
                if response not in ERROR_CODES and len(response) == 3:
                    sent_successfully = True

            if (not sent_successfully):
                # Resend command (because no response was ever got)
                self.to_robot(opcode_string)

        return

    def to_robot(self, message):
        # Send command
        self.comn.write(message)

    def write(self, sig, opcode, arg, ret="unknown"):
        """
        Public interface for sending opcodes to the robot
        """

        if self.isConnected:
            self.ready = False

            self.write_queue.put({
                'return': ret,
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
        self.camera = Camera()
        self.write_thread = Thread(target=self.write_stream)
        self.read_thread = Thread(target=self.read_stream)
        self.read_thread.start()
        self.write_thread.start()
        super(RobotComms, self).__init__(port)

    def gclose(self):
        self.camera.close()
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
        self.write(TEAM, STOP, 0, ret=RETURN_CODE["STOP"])

    def forward(self, speed):
        self.write(TEAM, FORWARD, int(speed), ret=RETURN_CODE["FORWARD"])

    def backward(self, speed):
        self.write(TEAM, BACKWARD, int(speed), ret=RETURN_CODE["BACKWARD"])

    def left(self, speed):
        self.write(TEAM, LEFT, int(speed), ret=RETURN_CODE["LEFT"])

    def right(self, speed):
        self.write(TEAM, RIGHT, int(speed), ret=RETURN_CODE["RIGHT"])

    def kick(self, speed):
        self.write(TEAM, KICK, int(speed), ret=RETURN_CODE["KICK"])

    def grab(self, speed):
        self.write(TEAM, GRAB, int(speed), ret=RETURN_CODE["GRAB"])

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


    def open(self):
        self.write(TEAM, OPEN, 80, ret = RETURN_CODE["OPEN"])

    def close(self):
        self.write(TEAM, CLOSE, 80, ret = RETURN_CODE["CLOSE"])


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

    # x - forward distance
    # y - right distance
    # z angle to the right of x
    # Note: this function is perfect for validating if communications work
    #       without flaws
    def xyzmove(self, x, y, z):
        x = int(x)
        y = int(y)
        z = int(z)

        command = ""

        if x > 0:
            command += "forward " + str(abs(x)) + " $ stop $ "
        elif x < 0:
            command += "backward " + str(abs(x)) + " $ stop $ "

        total_turn = 0
        turn = 90

        if y > 0:
            total_turn += turn
            command += "right " + str(turn) + " $ "
            command += "forward " + str(abs(y)) + " $ stop $ "
        elif y < 0:
            total_turn -= turn
            command += "left " + str(turn) + " $ "
            command += "forward " + str(abs(y)) + " $ stop $ "
        angle_remaining = (z - total_turn) % 360

        # Mod 360 to avoid treachery
        if angle_remaining <= 180:
            command += "right " + str(angle_remaining)
        else:
            command += "left " + str(360 - angle_remaining)

        self.compose(command)




    #rotate, move and grab
    def move_and_grab(self):

        distance = 10
        while(distance >=10):
            command = ""
            (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

            v1 = robot_coordinates
            v2 = ball_coordinates

            theta = self.angle_a_to_b(v1,v2)
            theta2 = self.angle_a_to_b(robot_dir_vector, (0.0, 0.0))
            angle = theta2 - theta

            turn = math.degrees(theta2 - theta)
            distance = self.dist(v1,v2)

            if turn >0:
                command += "right " + str(int(angle)) + " $"
            else:
                command += "left " + str(abs(int(angle))) + " $"

            command += "forward " + str(int(0.8*distance))
            self.compose(command)

        # ball is now sufficiently close to grab

        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        v1 = robot_coordinates
        v2 = ball_coordinates

        theta = self.angle_a_to_b(v1,v2)
        theta2 = self.angle_a_to_b(robot_dir_vector, (0.0,0.0))
        angle = theta2 - theta

        turn = math.degrees(theta2 - theta)
        distance = self.dist(v1,v2)

        if turn >0:
            command += "right " + str(int(angle)) + " $"
        else:
            command += "left " + str(abs(int(angle))) + " $"

        command += "open $"
        command += "forward " + str(distance) + " $"
        command += "close $"

        print(command)
        self.compose(command)

    def rotate_kick(self):
        (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        v1 = robot_coordinates

        #angle between robot and goal
        theta = self.angle_a_to_b(v1, (-320*0.46, 0.0))
        theta2 = self.angle_a_to_b(robot_dir_vector, (1.0, 0.0))
        angle = theta2 - theta
        print(angle)


        command = ""

        if angle >= 0 and angle <= 180:
            command += "right " + str(int(angle)) + " $ "
        else:
            command += "left " + str(int(360 - angle)) + " $ "

        print(command)
        command += "kick 100 "
        self.compose(command)



    def angle_a_to_b(self, v1, v2):
        return math.atan2((v1[1]-v2[1]), (v1[0] - v2[0]))
        #returns angle between vector v1-v2 and positive x axis


    def dist(self, v1, v2):
        return  math.hypot(v1[0] - v2[0], v1[1] - v2[1])


if __name__ == "__main__":
    print("This class is not designed to be run by hand")
