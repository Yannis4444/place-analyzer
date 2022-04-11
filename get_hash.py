"""
Can be used to get the user hash from a pixel and time
"""
import logging
from typing import Tuple, List, Dict, Optional

import tqdm
from pandas import DataFrame

from data_handler import DataHandler


def get_hash(pixel: Tuple[int, int], time: float) -> Optional[str]:
    """
    Gets the hash for a user by checking which hash was the last one
    that changed the given pixel at the specified time.

    This will simply go through the data in reverse order until it gets the correct pixel change

    :param pixel: The pixel to check
    :param time: The time from which to get the last edit in seconds
    :return: The hash (None if none is found)
    """

    hashes = get_hashes([(pixel, time)])
    if hashes:
        return hashes[0]


def get_hashes(pixel_times: List[Tuple[Tuple[int, int], float]]) -> List[str]:
    """
    Gets the hashes for users by checking which hashes were the last ones
    that changed the given pixels at the specified times.

    This will simply go through the data in reverse order until it gets the correct pixel change

    :param pixel_times: A list of tuples with a pixel (tuple) and a time in seconds each.
    :return: A list of the found hashes
    """

    hashes: List[str] = []

    dh = DataHandler.instance()

    if dh.influx_connection is None:
        for df in dh.get_data_frames(reversed=True, progress_label="Searching user hash"):
            delete_indexes = []
            for i, (pixel, time) in enumerate(pixel_times):
                row = df.loc[(df["coordinate"] == f"{pixel[0]},{pixel[1]}") & (df["time"] <= time)].tail(1)
                if len(row):
                    logging.info(f"{row['user_id'].item()} placed {pixel} after {row['time'].item()} s ({row['timestamp'].item()})")
                    delete_indexes.append(i)
                    hashes.append(row["user_id"].item())

            pixel_times = [pt for i, pt in enumerate(pixel_times) if i not in delete_indexes]

            if not pixel_times:
                return hashes

        logging.warning(f"No Hashes found for {pixel_times}")

    else:
        for i, (pixel, time) in tqdm.tqdm(enumerate(pixel_times), desc="Searching user hash"):
            try:
                hashes.append(dh.influx_connection.query(f"SELECT last(user_id) as user_id from \"position_pixels\" WHERE x = '{pixel[0]}' AND y = '{pixel[1]}' AND time <= '{dh.influx_connection.time_to_str(time)}'").raw["series"][0]["values"][-1][-1])
            except (IndexError, KeyError):
                logging.warning(f"No Hash found for {pixel} - {pixel}")

    return hashes
