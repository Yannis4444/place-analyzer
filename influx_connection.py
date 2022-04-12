import datetime
import logging
import threading
import time
from typing import Optional, Dict, List, Generator, Tuple

from influxdb import InfluxDBClient
from influxdb.resultset import ResultSet


class InfluxConnection:
    """
    Connection to an influxdb
    """

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 8086,
                 username: str = 'root',
                 password: str = 'root',
                 database: str = 'place_pixels',
                 timeout: int = 600):
        """
        Creates a new connection object.
        """

        """
        Sets the connection to the given parameters.
        This has to be called once at the start to be able to use the connection.

        :param host: hostname to connect to InfluxDB, defaults to 'localhost'
        :param port: port to connect to InfluxDB, defaults to 8086
        :param username: user to connect, defaults to 'root'
        :param password: password of the user, defaults to 'root'
        :param database: database name to connect to, defaults to None, defaults to 'place_pixels'
        :param timeout: The timeout for the client
        """

        logging.info(f"Connecting to {database} on {host}:{port}")

        # create the connection
        self._client = InfluxDBClient(host=host, port=port, username=username, password=password, database=database, timeout=timeout)

        while True:
            try:
                # create the database and switch to it
                if database not in self._client.get_list_database():
                    self._client.create_database(database)
                    self._client.switch_database(database)
                    break
            except Exception as e:
                logging.error(f"Failed to establish connection to InfluxDB. Trying again: {e}")
                time.sleep(60)

        self._cached_measurements = []  # used for writing measurements in bulk


    def initialize(self):
        """
        Gets all the data from the downloaded data files and writes it to the InfluxDB.
        This has to be used once before using the Influx data
        """

        from data_handler import DataHandler

        dh = DataHandler.instance()

        for df in dh.get_data_frames(progress_label="writing to InfluxDB"):
            for row in df[["user_id", "pixel_color", "coordinate", "time"]].itertuples():
                self.write_pixel(row[4], row[1], row[3], row[2], write_now=(row[0] % 100000) == 99999)

            self.write_cached_points()

    @property
    def client(self) -> Optional[InfluxDBClient]:
        """
        The InfluxDBClient used by the connection.
        This is None until set_connection is called

        :return: The InfluxDBClient object
        """

        return self._client

    def query(self, query: str, chunk_size: Optional[int] = 1000) -> ResultSet:
        """
        Sends a given query to the InfluxDB.
        In most cases get_data should be used

        :raises RuntimeError if the connection is not set
        :param query: The actual query string
        :param chunk_size: The size of the chunks
        :return: The queried data
        """

        logging.info(f"Running query: {query}")

        if self._client is None:
            raise RuntimeError("The InfluxDB connection was not yet set. Please call set_connection first")

        return self._client.query(query, chunked=chunk_size is not None, chunk_size=chunk_size)

    def str_to_time(self, time_str: str) -> float:
        """
        Converts a time string as used by Influx to a unix timestamp

        :param time_str: The time string
        :return: The unix timestamp
        """

        try:
            return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError:
            return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp()

    def time_to_str(self, timestamp: float) -> str:
        """
        Converts a unix timestamp to a time string as used by Influx

        :param timestamp: The unix timestamp
        :return: The time string
        """

        return str(datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)).rsplit("+", 1)[0]

    def write_pixel(self, time: float, user_id: str, pixel: str, color: str, write_now=True) -> bool:
        """
        Writes a pixel to the InfluxDB

        :param time: The time of the data point
        :param user_id: The user id
        :param pixel: The pixel as a comma seperated str
        :param color: The color as a hex string
        :param write_now: If this is set to false, the data point will not be written right away but together with the next one with write_now set to True
        :return: True, if the operation is successful
        """

        x, y, *r = pixel.split(",")

        x = int(x)
        y = int(y)

        if r:
            for i in range(x, int(r[0]) + 1):
                for j in range(y, int(r[1]) + 1):
                    self.write_pixel(time, user_id, f"{i},{j}", color, write_now=False)

            if write_now:
                self.write_cached_points()

        # prepare the data to be sent to the InfluxDB
        # split into two measurements as the influxDB can't handle this otherwise
        self._cached_measurements.append({
            "measurement": "user_pixels",
            "tags": {
                "user_id": user_id
                # "x": x,
                # "y": y
                # "color": color
            },
            "time": self.time_to_str(time),
            "fields": {
                # "pixel": pixel,
                "x": x,
                "y": y,
                "color": color
                # "user_id": user_id
            }
        })
        self._cached_measurements.append({
            "measurement": "position_pixels",
            "tags": {
                # "user_id": user_id
                "x": x,
                "y": y
                # "color": color
            },
            "time": self.time_to_str(time),
            "fields": {
                # "pixel": pixel,
                "color": color,
                "user_id": user_id
            }
        })

        if not write_now:
            return True

        # just save this one
        return self.write_cached_points()

    def write_cached_points(self, batch_size=1000):
        """
        Writes all currently cached data

        :param batch_size: The size of the batches to save in
        :return: True if successful
        """

        logging.debug(f"Writing {len(self._cached_measurements)} cached points")

        try:
            result = self._client.write_points(self._cached_measurements, time_precision="ms", batch_size=batch_size)
        except Exception as e:
            # wait ten seconds and try again
            logging.warning(f"Writing points failed. Trying again: {e}")
            time.sleep(10)
            return self.write_cached_points(batch_size=batch_size)

        if result:
            self._cached_measurements = []
            logging.debug("Done writing points")
        else:
            logging.warning("Writing points failed")

        return result

    def get_data(self, user_ids: Optional[List[str]] = None, pixel: Optional[str] = None, include_void=True, reversed=False, progress_label="Processing Data") -> Generator[Tuple[str, str, str, int], None, None]:
        """
        Gets data from the InfluxDB

        :param user_ids: An optional list of user ids to filter the results for
        :param pixel: A pixel to select
        :param include_void: If the pixels from the white void should be kept
        :param reversed: If reversed is set to True, the files and data will be returned in reverse order
        :param progress_label: The text to show in front of the progress bar
        :return: The result
        """

        # TODO: progress bar

        # start the query string
        query = f"SELECT time, user_id, color, x, y FROM \"{'user_pixels' if pixel is None else 'position_pixels'}\""

        if user_ids is not None or pixel is not None or not include_void:
            query += " WHERE"

        if user_ids is not None:
            query += " ("
            query += " OR ".join([f"user_id = '{i}'" for i in user_ids])
            query += ")"

        if pixel is not None:
            if user_ids is not None:
                query += " AND"

            query += " x = {} AND y = {}".format(*pixel.split(","))

        if not include_void:
            if user_ids is not None or pixel is not None:
                query += " AND"

            from data_handler import DataHandler

            query += f" time <= {self.time_to_str(DataHandler.instance().void_time)}"

        if reversed:
            query += "ORDER BY time DESC"

        # TODO: maybe not return position as str but x and y as int
        for t, user_id, color, x, y in self.query(query).raw["series"][0]["values"]:
            yield self.str_to_time(t), user_id, color, f"{x},{y}"
