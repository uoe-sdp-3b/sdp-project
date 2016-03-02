#!/usr/bin/env python2.7
import logging
from Queue import Queue
from planning.world import WorldApi
from plan.planner import Planner
from communication.communications import RobotComms
import time

logging.basicConfig(format='%(asctime)s - %(levelname)-7s %(name)-20s %(message)s', datefmt='%I:%M:%S')
log = logging.getLogger(__name__)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial",
                        help="Serial Port for RobotComms",
                        default="/dev/ttyACM0")
    parser.add_argument("-v", "--verbose",
                        help="Run in debug mode",
                        action='store_true')

    parser.add_argument("-c", "--color",
                        help="Our color",
                        required=True,
                        choices=["green", "pink"])

    return parser.parse_args()


class Tmp():
    queue = Queue()
    def __init__(self):
        pass

    def compose(self, thing):
        log.debug(">>" + thing)

def planner():
    args = parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    log.debug("Starting up...")
    robot = RobotComms(args.serial)
    # robot = Tmp()
    log.debug("Robot Configured")
    world = WorldApi(debug=args.verbose)

    try:
        log.debug('Entering Try-Catch')
        pl = Planner(world, args.color, robot=robot, debug=args.verbose)
        time.sleep(3)
        # pl.get_ball()
        # pl.get_to((0,0))
        # pl.receive_pass()
        pl.receive_turn_pass()
    except:
        raise

    return pl


if __name__ == "__main__":
    planner()
