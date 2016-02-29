#!/usr/bin/env python2.7
import logging
from vision.camera import Camera
from planning.world import WorldApi
from plan.planner import Planner
from communication.communications import RobotComms

logging.basicConfig(format='%(asctime)s - %(levelname)-7s %(name)-20s %(message)s', datefmt='%I:%M:%S')
log = logging.getLogger(__name__)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial",
                        help="Serial Port for RobotComms",
                        default="/dev/ttyACM0")
    parser.add_argument("--calibration",
                        help="Calibration config file for the camera",
                        default="./config/undistort_pitch0.json")
    parser.add_argument("-v", "--verbose",
                        help="Run in debug mode",
                        action='store_true')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    log.debug("Starting up...")
    camera = Camera(config=args.calibration)
    log.debug("Camera configured")
    # robot = RobotComms(args.serial, camera)
    robot = None
    log.debug("Robot Configured")
    world = WorldApi(debug=args.verbose)

    try:
        pl = Planner(world, robot=robot, debug=args.verbose)
        log.debug("Test move and grab")
        pl.move_and_grab()
        log.debug("Test rotate kick")
        pl.rotate_kick()
    finally:
        log.debug("Cleaning up...")
        pl.close()

if __name__ == "__main__":
    main()
