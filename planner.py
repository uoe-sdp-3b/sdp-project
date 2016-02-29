#!/usr/bin/env python2.7
import logging
from planning.world import WorldApi
from plan.planner import Planner

logging.basicConfig(format='[%(asctime)s][%(levelname)s](%(name)s) %(message)s', datefmt='%I:%M:%S')
log = logging.getLogger(__name__)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",
                        help="Run in debug mode",
                        action='store_true')

    return parser.parse_args()

def main():
    args = parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
    try:
        world = WorldApi(debug=args.verbose)
        pl = Planner(world, debug=args.verbose)
        log.debug("Test move and grab")
        pl.move_and_grab()
        log.debug("Test rotate kick")
        pl.rotate_kick()
    finally:
        log.debug("Cleaning up...")
        pl.close()

if __name__ == "__main__":
    main()
