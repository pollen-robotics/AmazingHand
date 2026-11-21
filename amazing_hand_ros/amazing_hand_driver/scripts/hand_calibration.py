#!/usr/bin/env python3
"""Validate the servo IDs and calibration angles supplied for this hand."""
import argparse
from math import isfinite

import yaml


def calibration(side, servo_ids, middle_pos):
    if side not in (1, 2):
        raise ValueError('side must be 1 (right) or 2 (left)')
    default_ids = list(range(1, 9)) if side == 1 else [15, 16, 13, 14, 11, 12, 17, 18]
    ids = yaml.safe_load(servo_ids) if servo_ids else default_ids
    if (not isinstance(ids, list) or len(ids) != 8 or
            any(type(i) is not int or not 0 <= i <= 253 for i in ids) or len(set(ids)) != 8):
        raise ValueError('servo_ids must contain eight unique integers in [0,253]')
    middle = yaml.safe_load(middle_pos)
    if (not isinstance(middle, list) or len(middle) != 8 or
            any(type(v) not in (int, float) or not isfinite(v) for v in middle)):
        raise ValueError('Hardware requires an explicit middle_pos list of eight finite angles in degrees, in ascending physical servo ID order')
    return ids, middle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('side', type=int)
    parser.add_argument('servo_ids')
    parser.add_argument('middle_pos')
    args = parser.parse_args()
    _, angles = calibration(args.side, args.servo_ids, args.middle_pos)
    print(angles)  # YAML list for the ROS 1 parameter server
