"""
This module is responsible for everything regarding the actual r/place data.
"""
import argparse
import gzip
import logging
import os
import threading
import urllib
from typing import Optional, List

import requests
from tqdm import trange


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

        # all csv data files
        self.data_files: List[str] = []

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

        for i in trange(78, desc="Downloading data", mininterval=0):
            url = url_template.format(i)
            filename = "data/" + url.rsplit("/", 1)[-1].replace(".gzip", "")
            self.data_files.append(filename)

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
