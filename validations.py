"""
Includes functions to ensure some things about the command line arguments.
"""

import argparse
from typing import Tuple


def validate_pixel(pixel: str) -> Tuple[int, int]:
    """
    Checks that the given string is a valid pixel (two integers seperated by a comma).

    :param pixel: The commandline argument
    :return: The pixel as a tuple
    :raises: argparse.ArgumentTypeError: if the argument is invalid
    """

    try:
        x, y = pixel.split(",")
        return int(x), int(y)
    except:
        raise argparse.ArgumentTypeError(f"\"{pixel}\" is not a valid pixel. The correct format is \"x,y\".")


def validate_time(time: str) -> int:
    """
    Checks that the given string is a valid time (hours and minutes seperated by a ':').

    :param time: The commandline argument
    :return: The time in seconds
    :raises: argparse.ArgumentTypeError: if the argument is invalid
    """

    try:
        h, m = time.split(":")
        return 60 * 60 * int(h) + 60 * int(m)
    except:
        raise argparse.ArgumentTypeError(f"\"{time}\" is not a valid time. The correct format is \"hh:mm\".")
