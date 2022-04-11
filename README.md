# r/place Analyzer
A script that can analyze different aspects from r/place and create statistics for users or communities.

## Dependencies

```
pip install requests
pip install tqdm
pip install pandas
pip install pillow
pip install influxdb
```

## Getting your User ID

The data provided by Reddit does not include usernames.
Instead, each user has an individual hash.
If you know a pixel that you placed, you can simply use `python main.py gethash -p 422,1135 -t 69:42`
with a pixel specified with `-p` and a time specified with `-t`.
For the time of a pixel you can best search on [r/place](https://www.reddit.com/r/place/?cx=1000&cy=810&px=731&ts=1649112460185) directly.

You can also use the `-p 422,1135-80:44` (`x,y-hh:mm`) for commands like `user` to get the user id before analyzing the data.

If you do not know a pixel that you placed you can try to find your username in the [data from the Internet Archive](https://archive.org/details/place2022-opl-raw).
Just open the data in a text editor and search for your name.

## InfluxDB

### Why InfluxDB?

You can optionally write the data to an InfluxDB to increase efficiency.
This will also allow you to use InfluxQL to query for other data.

Querying for the pixels of one user using a known pixel can take about an hour without InfluxDB.
Using the InfluxDB the same operation takes no longer than a second.

### How to use it

If you do not have an existing InfluxDB available, one can easily be started using the included `docker-compose.yml`.
If you use an existing installation, you might need to set `max-values-per-tag = 0` and
`max-series-per-database = 0` to allow for the user_ids as tags.
Also keep an eye on the memory usage of the container.
You can edit the limit in the `docker-compose.yml`.

To use the InfluxDB as a data source, simply add `-i user:password@host:port`
(`-i admin:admin@localhost:8086` for the included `docker-compose.yml`) to the end of your command.

Before you can use the InfluxDB functionality, you need to initialize the data by running
`python main.py influxdb -i user:password@host:port` once.
Note that it will take some time to write all the data to the InfluxDB (about 2.5 h for me).
After the initial data collection, everything will be much faster.

### How it works

Using InfluxDB with the script will create a `place_pixels` database with a `user_pixels`
and a `position_pixels` measurement.
Both measurements will consist of the following:
 - `time`: The time of the pixel placement
 - `color`: The color of the placed pixel
 - `x`: The x coordinates of the pixel
 - `y`: The y coordinates of the pixel
 - `user_id`: The hashed user id

InfluxDB does not like to many series and adding many tags leads to too many series to handle on a regular computer.
As tags are needed in order to perform queries that don't take ages, two measurements are created.
In `user_pixels` the `user_id` is a tag and can efficiently be queried.
`x` and `y` are the tags for `position_pixels`.
A combination of queries on both measurements can be used for further searches.