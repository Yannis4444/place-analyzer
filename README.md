# r/place Analyzer
A script that can analyze different aspects from r/place and create statistics for users or communities (coming soon).

## Dependencies

To use the script you will need to install the following packages:

```
pip install requests
pip install tqdm
pip install pandas
pip install pillow
pip install influxdb
```

## User based analysis

One of the available options is to analyse the pixels placed by a specific user or a group of users.

### TL;DR

To just get some visualizations, the following command should work.
Note that this will take quite a while the first time as all the data has to be downloaded.
I would also advise to take a look at the [InfluxDB](#InfluxDB) functionality below for increased efficiency.

```
python main.py user -n <username> -i admin:admin@localhost:8086 -d -b -t 0.05 -c "#FFFF00" -g 60
```

For more information about the different options, keep reading or add the `-h` flag to show the help message.

### Getting your User ID

The data provided by Reddit does not include usernames.
Instead, each user has an individual hash.
In order to analyse a user's activity, we first need to find out the corresponding user hash.
This can be done one of a few ways

#### Using a known pixel

If you know a pixel that you placed, you can simply use `python main.py gethash -p x,y-hh:mm`
(example: `420,69-69:42`) with a pixel and time.
For the time of a pixel you can best search the canvas on [r/place](https://www.reddit.com/r/place/) directly.

You can also use `-p x,y-hh:mm` for commands like `user` to get the user id before analyzing the data.
Note that this will get the user hash each time.
Therefore, it is advised to add the user hash with the `-u` flag once it is known.

#### Searching by username

If you do not know a pixel that you placed you can try to find your username in the
[data from the Internet Archive](https://archive.org/details/place2022-opl-raw).

To do this, you can use `python main.py gethash -n <username>` or simply add `-n <username>` to a command like `user` directly.
Note that this will download the data from the Internet Archive and can therefore take a while the first time.

The results of this are saved in `hash_aliases.ini` and will therefore only be gotten once.

#### Aliases

Once you have a user hash, you can add an alias for it with the following command:

```
python main.py setalias <hash> <alias>
```

This will allow you to use `-n <alias>` afterwards.
Searching for a hash by username, will automatically add an alias for it.
It is advised to use the reddit username as an alias.

### Getting Data

To analyze a user's activity you will have to call `python main.py user [OPTIONS]`.
This command can take many flags that are also shown in the commands help page:

#### User Selection

You can specify as many users as you would like for this command and will get individual as well as combined data.
You have multiple options to specify a user:

- `-u <hash>`, `--user-id <hash>`: If you know the users hash (for example from the `gethash` command), you can use it as a selector
- `-p <x,y-hh:mm>`, `--pixel <x,y-hh:mm>`: Specify a known pixel to search the user hash from. For details see [Using a known pixel](#Using-a-known-pixel)
- `-n <username>`, `--username <username>`: Search a user using a username. For details see [Searching by username](#Searching-by-username)

#### Output

- `-o <dir>`, `--output <dir>`: A directory for the output files. (default: out/)

#### Data

- `-d`, `--include-void`: Include The pixels placed as a part of the white void at the end.

#### Visuals:

- `-m <file>`, `--background-image <file>`: The image to use as the background. (default: resources/final_place.png)
- `-b`, `--background_black_white`: Turn the background black and white.
- `-t <value>`, `--background-image-opacity <value>`: The opacity of the background image. (default: 0.1)
- `-l <color>`, `--background-color <color>`: The color for the background. (default: #000000)
- `-c <color>`, `--highlight-color <color>`: The color for the highlighted pixels. The color of the placed pixel is used if not specified.

#### GIF:

- `-g <length>`, `--gif-length <length>`: If specified, a gif of the given length will be created.

#### InfluxDB:

- `-i <connection>`, `--influx <connection>`: Use InfluxDB for the data. This will greatly increase the performance. Format: user:password@host:port. For details see [InfluxDB](#InfluxDB)

### Examples

These are a few examples that I created for myself and a few friends.

#### All my pixels in yellow on a black and white background

```
python main.py user -u XxWx6C5rbZCI0934WfTTaAbkAkMUn+bpUp4RHvvOBqGlV3OndgGYiQVoPLkyGiOi+UAGxez84E4o6wCndt1RpA== -i admin:admin@localhost:8086 -d -b -t 0.05 -c "#FFFF00"
```
or
```
python main.py user -p 422,1135-69:42 -i admin:admin@localhost:8086 -d -b -t 0.05 -c "#FFFF00"
```
or
```
python main.py user -n Yannis4444 -i admin:admin@localhost:8086 -d -b -t 0.05 -c "#FFFF00"
```

The different options will work for all other examples but aren't included for all

<p align="center">
    <img alt="example" src="examples/Yannis4444/canvas_0_05_#000000_#FFFF00_bw.png" title="share_sheet" width="800"/>
</p>

#### The same as a sixty-second-long gif

```
python main.py user -n Yannis4444 -i admin:admin@localhost:8086 -d -b -t 0.05 -c "#FFFF00" -g 60
```

<p align="center">
    <img alt="example" src="examples/Yannis4444/canvas_0_05_#000000_#FFFF00_bw.gif" title="share_sheet" width="800"/>
</p>

#### Combined Data for a group of people with a colored background without data from the final void

```
python main.py user -n Yannis4444 -n <friend1> -n <friend2> -n <friend3> -i admin:admin@localhost:8086 -c "#FFFF00"
```

<p align="center">
    <img alt="example" src="examples/combined/canvas_0_1_#000000_#FFFF00_novoid.png" title="share_sheet" width="800"/>
</p>

#### Pixels in the correct color

```
python main.py user -n Yannis4444 -i admin:admin@localhost:8086 -d
```

<p align="center">
    <img alt="example" src="examples/Yannis4444/canvas_0_1_#000000_original.png" title="share_sheet" width="800"/>
</p>

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