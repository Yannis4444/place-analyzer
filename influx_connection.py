import datetime
import logging
import threading
import time
from typing import Optional, Dict, List

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
                 database: str = 'place_pixels'):
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
        :param database: database name to connect to, defaults to None, defaults to 'measurements'
        """

        logging.info(f"Connecting to {database} on {host}:{port}")

        # create the connection
        self._client = InfluxDBClient(host=host, port=port, username=username, password=password, database=database)

        # create the database and switch to it
        if database not in self._client.get_list_database():
            self._client.create_database(database)
            self._client.switch_database(database)

        self._cached_measurements = []  # used for writing measurements in bulk

    @property
    def client(self) -> Optional[InfluxDBClient]:
        """
        The InfluxDBClient used by the connection.
        This is None until set_connection is called

        :return: The InfluxDBClient object
        """

        return self._client

    def query(self, query: str) -> ResultSet:
        """
        Sends a given query to the InfluxDB.
        In most cases get_data should be used

        :raises RuntimeError if the connection is not set
        :param query: The actual query string
        :return: The queried data
        """

        if self._client is None:
            raise RuntimeError("The InfluxDB connection was not yet set. Please call set_connection first")

        return self._client.query(query)

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
        data = {
            "measurement": "pixels",
            "tags": {
                "user_id": user_id,
                "x": x,
                "y": y,
                "color": color
            },
            "time": datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc),
            "fields": {
                # "pixel": pixel,
                "color": color
                # "user_id": user_id
            }
        }

        if not write_now:
            # just add this to the list to be saved later and return True
            self._cached_measurements.append(data)
            return True

        if self._cached_measurements:
            # There are cached measurements to be saved together with this one
            result = self._client.write_points(self._cached_measurements + [data])
            if result:
                self._cached_measurements = []
            return result

        # just save this one
        return self._client.write_points([data])

    def write_cached_points(self, batch_size=1000):
        """
        Writes all currently cached data

        :param batch_size: The size of the batches to save in
        :return: True if successful
        """

        logging.info(f"Writing {len(self._cached_measurements)} cached points")

        result = self._client.write_points(self._cached_measurements, batch_size=10000)
        if result:
            self._cached_measurements = []
            logging.info("Done writing points")
        else:
            logging.warning("Writing points failed")

        return result

    def get_data(self, user_ids: Optional[List[str]] = None, pixel: Optional[str] = None, min_time: Optional[int] = None, max_time: Optional[int] = None) -> ResultSet:
        """
        Gets data from the InfluxDB

        :return: The result
        """

        # TODO: use parameters

        # start the query string
        query = f"SELECT time, user_id, pixel, color FROM \"pixels\""

        logging.info(f"Running query: {query}")

        return self.query(query)
