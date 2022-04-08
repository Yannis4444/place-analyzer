"""
This module is responsible for everything regarding the actual r/place data.
"""
import argparse
import datetime
import gzip
import logging
import os
import threading
import urllib
from collections import OrderedDict
from typing import Optional, List, Generator, Dict

import pandas as pd
from pandas import DataFrame
from tqdm import trange, tqdm


class DataHandler:
    """
    Takes care of getting data from reddit.
    This is a singleton.
    """

    _singleton_lock = threading.Lock()
    _instance: 'DataHandler' = None

    @classmethod
    def instance(cls) -> 'DataHandler':
        """
        Returns the data handler singleton

        :return: The data handler instance
        """

        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """
        Creates a new data handler.
        This should not be called directly as this is a singleton.

        :raises RuntimeError if called directly a second time
        """

        if DataHandler._instance is not None:
            raise RuntimeError(f"{self.__name__} is a singleton")
        else:
            DataHandler._instance = self

        self.args: Optional['argparse.Namespace'] = None

        # the start time from r/place
        self.start_time = 1648817027.221

        # all csv data files under their index
        self.data_files: Dict[int, str] = OrderedDict()

    def set_args(self, args: 'argparse.Namespace'):
        """
        Sets the command line args.

        :param args: The args
        """

        self.args = args

    def download_data(self):
        """
        Downloads all the data from Reddit and saves it to the data folder.
        Also unzips the data.

        From https://www.reddit.com/r/place/comments/txvk2d/rplace_datasets_april_fools_2022/:
        "The data is available in 78 separate files at
        https://placedata.reddit.com/data/canvas-history/2022_place_canvas_history-000000000000.csv.gzip
        through
        https://placedata.reddit.com/data/canvas-history/2022_place_canvas_history-000000000077.csv.gzip"
        """

        # create directory
        if not os.path.isdir("data"):
            os.makedirs("data")

        url_template = "https://placedata.reddit.com/data/canvas-history/2022_place_canvas_history-{:012d}.csv.gzip"

        # Why not change things up and put the data in a totally random order!?
        # That seems like fun and wont annoy anyone working with the data - right?
        # for i in trange(78, desc="Downloading data", mininterval=0):
        for i in tqdm([1, 2, 3, 5, 6, 10, 11, 8, 13, 4, 9, 15, 12, 18, 14, 16, 20, 17, 23, 19, 21, 28, 7, 29, 30, 31, 32, 33, 25, 35, 36, 27, 22, 0, 40, 41, 24, 34, 44, 37, 38, 39, 48, 43, 26, 45, 46, 47, 42, 49, 50, 55, 52, 57, 58, 54, 61, 56, 63, 53, 59, 60, 62, 51, 70, 64, 65, 66, 72, 73, 74, 75, 76, 77, 67, 69, 68, 71],
                      desc="Downloading data", mininterval=0):
            url = url_template.format(i)
            filename = "data/" + url.rsplit("/", 1)[-1].replace(".gzip", "")
            self.data_files[i] = filename

            # skip if the file already exists
            if os.path.isfile(filename):
                logging.debug(f"Skipping {filename} as it was already downloaded before")
                continue

            logging.debug(f"Downloading {filename}")

            try:
                # download and extract
                with urllib.request.urlopen(url) as response:
                    with gzip.GzipFile(fileobj=response) as uncompressed:
                        file_content = uncompressed.read()

                # write to file
                with open(filename, 'wb') as f:
                    f.write(file_content)

            except Exception as e:
                logging.error(f"Failed to download {filename}")
                logging.exception(e)

    def _str_to_time(self, time_str: str) -> float:
        """
        Converts the time strings as given by the data to the time since the start in seconds

        :param time_str: The time string as given by the data
        :return: The time since the start in seconds
        """

        try:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f %Z").replace(tzinfo=datetime.timezone.utc).timestamp() - self.start_time
        except ValueError:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=datetime.timezone.utc).timestamp() - self.start_time

    def _convert_data(self, df: DataFrame) -> DataFrame:
        """
        Converts a given data frame to a more usable format.
        This will convert the time strings to the time since the start in seconds.

        :param df: The original data frame
        :return: The new data frame
        """

        df["time"] = df["timestamp"].apply(self._str_to_time).astype("int")

        return df

    def get_data_frames(self, user_ids: Optional[List[str]]=None, reversed=False) -> Generator[DataFrame, None, None]:
        """
        Creates pandas dataframes from the downloaded data.
        Each file will be a separate data frame as the Ram does not like the alternative.
        Will be empty if download_data was not called.

        :param user_ids: An optional list of user ids to filter the results for
        :param reversed: If reversed is set to True, the files will be returned in reverse order
        :return: The pandas dataframes
        """

        # TODO: set text for progress bar
        for i in tqdm(list(self.data_files)[::-1] if reversed else self.data_files, desc="Processing Data"):
            yield self.get_data_frame(i, user_ids=user_ids)

    def get_data_frame(self, index: int, user_ids: Optional[List[str]]=None):
        """
        Creates a pandas dataframe from the downloaded data.
        The index specifies which of the csv files should be used

        :param index: The index of the file to use
        :param user_ids: An optional list of user ids to filter the results for
        :raises: IndexError if no data file with the given index exists
        :return: The pandas dataframe
        """

        user_ids = list(dict.fromkeys(user_ids))

        if index not in self.data_files:
            raise IndexError(f"A data file with the index {index} does not exist.")

        df = self._convert_data(pd.read_csv(self.data_files[index], sep=","))

        df["coordinate"] = df["coordinate"].astype("str")

        # select only specified user ids
        if user_ids is not None:
            df = df.loc[df["user_id"].isin(user_ids)]

        return df
