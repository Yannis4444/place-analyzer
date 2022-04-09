# r/place Analyzer
A script that can analyze different aspects from r/place and create statistics for users or communities.

# Getting your User ID

The data provided by reddit does not include usernames.
Instead, each user has an individual hash.
If you know a pixel that you placed, you can simply use `python main.py gethash -p 422,1135 -t 69:42`
with a pixel specified with `-p` and a time specified with `-t`.
For the time of a pixel you can best search on [r/place](https://www.reddit.com/r/place/?cx=1000&cy=810&px=731&ts=1649112460185) directly.

You can also use the `-p 422,1135-80:44` (`x,y-hh:mm`) for commands like `user` to get the user id before analyzing the data.

If you do not know a pixel that you placed you can try to find your username in the [data from the Internet Archive](https://archive.org/details/place2022-opl-raw).
Just open the data in a text editor and search for your name.

# Dependencies

```
pip install requests
pip install tqdm
pip install pandas
pip install pillow
```
