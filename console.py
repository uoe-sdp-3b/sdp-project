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
            if message:
                return message.strip()
        return None

    def write(self, message):
        if message == "":
            return

        args = message.split(" ")
        f = getattr(self.robot, args[0], None)

        try:
            if f and len(args) > 1:
                f(*args[1:])
            elif f:
                f()
            else:
                self.robot.queue.put("argument: '%s' doesn't exist" % args[0])
        except TypeError as e:
            self.robot.queue.put(str(e))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="console for robot")
    parser.add_argument("-p", default="/dev/ttyACM0")

    args = parser.parse_args()

    console = Console(args.p)
    console.start()


if __name__ == "__main__":
    main()
