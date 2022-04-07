"""
Can be used to get the user hash from a pixel and time
"""
from typing import Tuple, List, Dict, Optional

from pandas import DataFrame

from data_handler import DataHandler


def get_hash(pixel: Tuple[int, int], time: int) -> str:
    """
    Gets the hash for a user by checking which hash was the last one
    that changed the given pixel at the specified time.

    This will simply go through the data in reverse order until it gets the correct pixel change

    :param pixel: The pixel to check
    :param time: The time from which to get the last edit in seconds
    :return: The hash
    """

    pass

def get_hashes(pixel_times: List[Tuple[Tuple[int, int], int]]) -> List[str]:
    """
    Gets the hashes for users by checking which hashes were the last ones
    that changed the given pixels at the specified times.

    This will simply go through the data in reverse order until it gets the correct pixel change

    :param pixel_times: A list of tuples with a pixel (tuple) and a time in seconds each.
    :return: A list of the found hashes
    """
    return

    hashes: Dict[Tuple[Tuple[int, int], int], Optional[str]] = {(): None for pt in pixel_times}

    for df in DataHandler.instance().get_data_frames(reversed=True):
        hash_missing = False

