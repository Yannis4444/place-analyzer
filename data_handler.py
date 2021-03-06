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
from typing import Optional, List, Generator, Dict, Tuple
from urllib.request import urlopen

import pandas as pd
from pandas import DataFrame
from tqdm import trange, tqdm

from influx_connection import InfluxConnection


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
        self.void_time = 1649112460.157
        self.end_time = 1649116847.206

        # all csv data files under their index
        self.data_files: Dict[int, str] = OrderedDict()

        self.influx_user: Optional[str] = None
        self.influx_password: Optional[str] = None
        self.influx_host: Optional[str] = None
        self.influx_port: Optional[int] = None
        self.influx_connection: Optional[InfluxConnection] = None

    def set_args(self, args: 'argparse.Namespace'):
        """
        Sets the command line args.

        :param args: The args
        """

        self.args = args

        if args.influx is not None:
            influx_split = args.influx.split("@")
            self.influx_user, self.influx_password = influx_split[0].split(":")
            self.influx_host, port_str = influx_split[1].split(":")
            self.influx_port = int(port_str)

            self.influx_connection = InfluxConnection(self.influx_host, self.influx_port, self.influx_user, self.influx_password)

    def time_to_timestamp(self, time: float) -> float:
        """
        Calculates the corresponding unix timestamp
        for the time since the beginning of r/place in s

        :param time: The time since the beginning in s
        :return: The timestamp
        """

        return self.start_time + time

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
        for i in trange(79, desc="Downloading data", mininterval=0):
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
                exit(-1)

    def _str_to_time(self, time_str: str) -> float:
        """
        Converts the time strings as given by the data to a unix timestamp

        :param time_str: The time string as given by the data
        :return: The unix timestamp
        """

        try:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f %Z").replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=datetime.timezone.utc).timestamp()

    def _convert_data(self, df: DataFrame) -> DataFrame:
        """
        Converts a given data frame to a more usable format.
        This will convert the time strings to the time since the start in seconds.

        :param df: The original data frame
        :return: The new data frame
        """

        if "time" not in df.columns:
            df["time"] = df["timestamp"].apply(self._str_to_time).astype("float")

        return df

    def get_data(self, user_ids: Optional[List[str]] = None, pixel: Optional[str] = None, include_void=True, reversed=False, progress_label="Processing Data") -> Generator[Tuple[str, str, str, int], None, None]:
        """
        Get all the data .

        :param user_ids: An optional list of user ids to filter the results for
        :param pixel: A pixel to select
        :param include_void: If the pixels from the white void should be kept
        :param reversed: If reversed is set to True, the files and data will be returned in reverse order
        :param progress_label: The text to show in front of the progress bar
        :return: An iterator over the rows (Tuple of time, user_id, color, pixel)
        """

        if self.influx_connection is None:
            # use data frames from the files
            for df in self.get_data_frames(user_ids=user_ids, pixel=pixel, include_void=include_void, reversed=reversed, progress_label=progress_label):
                for row in df[["time", "user_id", "pixel_color", "coordinate"]].itertuples():
                    time = float(row[1])
                    user_id = str(row[2])
                    color = str(row[3])
                    pixel = str(row[4])

                    yield time, user_id, color, pixel

        else:
            # use Influx connection
            for x in self.influx_connection.get_data(user_ids=user_ids, pixel=pixel, include_void=include_void, reversed=reversed, progress_label=progress_label):
                yield x

    def get_data_frames(self, user_ids: Optional[List[str]] = None, pixel: Optional[str] = None, include_void=True, reversed=False, progress_label="Processing Data") -> Generator[DataFrame, None, None]:
        """
        Creates pandas dataframes from the downloaded data.
        Each file will be a separate data frame as the Ram does not like the alternative.
        Will be empty if download_data was not called.

        :param user_ids: An optional list of user ids to filter the results for
        :param pixel: A pixel to select
        :param include_void: If the pixels from the white void should be kept
        :param reversed: If reversed is set to True, the files and data will be returned in reverse order
        :param progress_label: The text to show in front of the progress bar
        :return: The pandas dataframes
        """

        for i in tqdm(list(self.data_files)[::-1] if reversed else self.data_files, desc=progress_label):
            yield self.get_data_frame(i, user_ids=user_ids, pixel=pixel, include_void=include_void, reversed=reversed)

    def get_data_frame(self, index: int, user_ids: Optional[List[str]] = None, pixel: Optional[str] = None, include_void=True, reversed=False):
        """
        Creates a pandas dataframe from the downloaded data.
        The index specifies which of the csv files should be used

        :param index: The index of the file to use
        :param pixel: A pixel to select
        :param user_ids: An optional list of user ids to filter the results for
        :param include_void: If the pixels from the white void should be kept
        :param reversed: If reversed is set to True, the data will be returned in reverse order
        :raises: IndexError if no data file with the given index exists
        :return: The pandas dataframe
        """

        if user_ids is not None:
            user_ids = list(dict.fromkeys(user_ids))

        if index not in self.data_files:
            raise IndexError(f"A data file with the index {index} does not exist.")

        df = self._convert_data(pd.read_csv(self.data_files[index], sep=","))

        df["coordinate"] = df["coordinate"].astype("str")

        # select only specified user ids
        if user_ids is not None:
            df = df.loc[df["user_id"].isin(user_ids)]

        if pixel is not None:
            df = df.loc[df["coordinate"] == pixel]

        if not include_void:
            df = df.loc[df["time"] < self.void_time]

        if reversed:
            return df.iloc[::-1]
        else:
            return df
