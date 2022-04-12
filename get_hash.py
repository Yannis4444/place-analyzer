"""
Can be used to get the user hash from a pixel and time
"""
import logging
from typing import Tuple, List, Dict, Optional

import tqdm
from pandas import DataFrame

from data_handler import DataHandler
from hash_alias_handler import HashAliasHandler
from username_finder import UsernameFinder


def get_hash_by_pixel(pixel: Tuple[int, int], time: float) -> Optional[str]:
    """
    Gets the hash for a user by checking which hash was the last one
    that changed the given pixel at the specified time.

    This will simply go through the data in reverse order until it gets the correct pixel change

    :param pixel: The pixel to check
    :param time: The time from which to get the last edit in seconds
    :return: The hash (None if none is found)
    """

    hashes = get_hashes_by_pixel([(pixel, time)])
    if hashes:
        return hashes[0]


def get_hashes_by_pixel(pixel_times: List[Tuple[Tuple[int, int], float]]) -> List[str]:
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
        for i, (pixel, time) in tqdm.tqdm(enumerate(pixel_times), desc="Searching user hash", mininterval=0):
            try:
                hashes.append(dh.influx_connection.query(f"SELECT last(user_id) as user_id from \"position_pixels\" WHERE x = '{pixel[0]}' AND y = '{pixel[1]}' AND time <= '{dh.influx_connection.time_to_str(time)}'").raw["series"][0]["values"][-1][-1])
            except (IndexError, KeyError):
                logging.info(f"No Hash found for {pixel} - {time}")

    return hashes


def get_hashes_by_username(usernames: List[str], points_with_canvas_id: int = 3, points_without_canvas_id: int = 20) -> List[str]:
    """
    Gets the hashes for a list of usernames by checking the data from the internet archive for placed pixels
    and then getting the hashes for these pixels.

    :param usernames: The usernames to search for
    :param points_with_canvas_id: How many points with a canvas id are needed to consider them complete
    :param points_without_canvas_id: How many points without a canvas id are needed to consider them complete
    :return: The hashes
    """

    final_hashes: List[str] = []
    left_usernames: List[str] = []

    hash_alias = HashAliasHandler.instance()

    # get the ones that were already gotten before
    for username in usernames:
        hash = hash_alias.get_hash_from_alias(username)
        if hash is None:
            left_usernames.append(username)
        else:
            final_hashes.append(hash)
            logging.info(f"Using saved hash {hash} for {username}")

    # List with possible hashes for user
    if left_usernames:
        user_hashes: Dict[str, List[str]] = {}
        for username, (canvas_id_pixels, other_pixels) in UsernameFinder().get_pixel_times(left_usernames, points_with_canvas_id=points_with_canvas_id, points_without_canvas_id=points_without_canvas_id).items():
            # first use ones with canvas id, then without, if both incomplete use the same order
            if len(canvas_id_pixels) >= points_with_canvas_id:
                user_hashes[username] = get_hashes_by_pixel([(x[0], x[1] + 0.2) for x in canvas_id_pixels])
            elif len(other_pixels) >= points_without_canvas_id:
                user_hashes[username] = get_hashes_by_pixel([(x[0], x[1] + 0.2) for x in other_pixels])
            elif canvas_id_pixels:
                user_hashes[username] = get_hashes_by_pixel([(x[0], x[1] + 0.2) for x in canvas_id_pixels])
            elif other_pixels:
                user_hashes[username] = get_hashes_by_pixel([(x[0], x[1] + 0.2) for x in other_pixels])
            else:
                logging.warning(f"Could not find {username} in the Data from the Internet Archive")

        for username, hashes in user_hashes.items():
            if not hashes:
                print(f"Could not get hash for {username}")
                continue

            most_frequent_hash = max(set(hashes), key=hashes.count)

            # warning if the number of hits is not significant
            if hashes.count(most_frequent_hash) == 1 and len(hashes) > 1:
                logging.warning(f"Hash for {username} is ambiguous")

            final_hashes.append(most_frequent_hash)

            # save this as an alias
            hash_alias.save_alias(most_frequent_hash, username)

    # add a little time to the timestamp to make sure we get the right one
    return final_hashes
