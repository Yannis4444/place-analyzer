import argparse
import logging
import sys
from typing import List, Optional, Dict

import get_hash
import validations
from data_handler import DataHandler
from hash_alias_handler import HashAliasHandler
from image_creator import ImageCreator
from username_finder import UsernameFinder


class PlaceAnalyzer:
    def __init__(self):
        """
        Gets all commandline arguments and validates them.

        :return: The arguments
        """

        parser = argparse.ArgumentParser(
            description='A script that can analyze different aspects from r/place and create statistics for users or communities.',
            usage=f"""{sys.argv[0]} <command> [OPTIONS]

Commands:
  gethash [OPTIONS]       Get the hashed identifier of a user as used
                          in the data using a username or known pixel.
  user [OPTIONS]          Analyze the activity of a user (or a
                          group of users).
  setalias <hash> <alias> Set the alias for a hash. This is used for filenames
                          and outputs as well as easier queries with the
                          -n <username> flag. Aliases are automatically set
                          when querying by username.
  influxdb [OPTIONS]      If you wish to use the InfluxDB functionality,
                          you need to execute this once before.
                          This will get write all the data to the InfluxDB.
                          This can take a few hours (2.5 h for me).
""")

        parser.add_argument('command', help="Command to run")

        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def add_default_options(self, parser: argparse.ArgumentParser, influxdb=False):
        """
        Adds default arguments to a parser like verbose and influx

        :param parser: The parser to add the options to
        :param influxdb: Set to true to make the influx flag required
        """

        parser.add_argument('-i', '--influx', required=influxdb, help="Use InfluxDB for the data. This will greatly increase the performance. A new \"place_pixels\" database will be created. Format: user:password@host:port", metavar="<connection>")
        parser.add_argument('-v', '--verbose', required=False, action='count', default=0, help="Enable verbose output (-vv for debug)")

    def set_logging(self, verbose: int):
        """
        Sets the logging level
         0: nothing
         1: info
         2: debug

        :param verbose: the logging level
        """

        # set logging level
        if verbose:
            logging.basicConfig(
                level=logging.DEBUG if verbose > 1 else logging.INFO,
                format='[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s',
            )
        else:
            logging.basicConfig(
                level=logging.WARNING,
                format='[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s',
            )

    def init_data_handler(self, args: argparse.Namespace) -> DataHandler:
        """
        Initialises the data handler

        :param: The command line parameters
        :return: The data handler
        """

        dh = DataHandler.instance()
        dh.set_args(args)
        dh.download_data()

        return dh

    def gethash(self):
        """
        Get the hashed identifier of a user
        as used in the data using a known pixel.
        """

        # get the options and set logging
        parser = argparse.ArgumentParser(description='Get the hash for a user by checking a specific pixel at a specific time. You will have to enter the coordinates and the time for a pixel of which you want to know the author. You can get the coordinates and the time in the canvas history here: https://www.reddit.com/r/place')
        parser.add_argument('-p', '--pixel', required=False, type=validations.validate_pixel_time, action="append", help="A known pixel and time to automatically get the user like gethash. x,y-hh:mm (example: \"420,69-69:42\").", metavar="<pixel>")
        parser.add_argument('-n', '--username', required=False, type=str, action="append", help="A Reddit username. If provided, the data from the Internet Archive will be searched for it and then if found the pixel will be searched in the normal data.", metavar="<name>")
        self.add_default_options(parser)
        args = parser.parse_args(sys.argv[2:])
        self.set_logging(args.verbose)
        dh = self.init_data_handler(args)

        # get all hashes
        user_ids: List[str] = []
        if args.pixel is not None:
            print("Getting user ids from known pixels")
            user_ids += get_hash.get_hashes_by_pixel([(p[0], dh.time_to_timestamp(p[1])) for p in args.pixel])
        if args.username is not None:
            print("Getting user ids from usernames")
            user_ids += get_hash.get_hashes_by_username(args.username)

        print("\n".join(user_ids))

    def get_filename(self, args: argparse.Namespace, user_id: str = None) -> str:
        """
        Generates a filename from the args
        :param args: The command line args
        :param user_id: The User Id (None for combined)
        :return: The filename
        """

        if user_id is None:
            user_id = "combined"

        name = f"canvas_{args.background_image_opacity}_{args.background_color}_{args.highlight_color or 'original'}{'' if args.include_void else '_novoid'}{'_bw' if args.background_black_white else ''}"

        return "{}/{}/{}.png".format(args.output, "".join(i for i in (HashAliasHandler.instance().get_alias_from_hash(user_id) or user_id) if i not in "\\/:*?<>|"), name)

    def user(self):
        """
        Analyze the activity of a user (or a
        group of users).
        """

        # get the options and set logging
        parser = argparse.ArgumentParser(description='Analyzes the activity of the specified users. Users can be specified using their user-id/hash (see gethash command) or using a known pixel just like gethash.')
        parser.add_argument('-u', '--user-id', required=False, type=str, action="append", help="The user-id/hash of a user to include", metavar="<user>")
        parser.add_argument('-p', '--pixel', required=False, type=validations.validate_pixel_time, action="append", help="A known pixel and time to automatically get the user like gethash. x,y-hh:mm (example: \"420,69-69:42\").", metavar="<pixel>")
        parser.add_argument('-n', '--username', required=False, type=str, action="append", help="A Reddit username. If provided, the data from the Internet Archive will be searched for it and then if found the pixel will be searched in the normal data.", metavar="<name>")
        parser.add_argument('-d', '--include-void', required=False, action='count', default=0, help="Include The pixels placed as a part of the white void at the end.")
        parser.add_argument('-o', '--output', required=False, type=str, help="A directory for the output files.", default="out/", metavar="<dir>")
        parser.add_argument('-b', '--background-image', required=False, type=str, help="The image to use as the background.", default="resources/final_place.png", metavar="<file>")
        parser.add_argument('-c', '--background_black_white', required=False, action='count', default=0, help="Turn the background black and white.")
        parser.add_argument('-a', '--background-image-opacity', required=False, type=float, help="The opacity of the background image.", default=0.1, metavar="<value>")
        parser.add_argument('-l', '--background-color', required=False, type=str, help="The color for the background.", default="#000000", metavar="<color>")
        parser.add_argument('-g', '--highlight-color', required=False, type=str, help="The color for the highlighted pixels. The color of the placed pixel is used if not specified", metavar="<color>")
        self.add_default_options(parser)
        args = parser.parse_args(sys.argv[2:])
        self.set_logging(args.verbose)
        dh = self.init_data_handler(args)

        # get all hashes to be used
        user_ids: List[str] = args.user_id or []
        if args.pixel is not None:
            print("Getting user ids from known pixels")
            user_ids += get_hash.get_hashes_by_pixel([(p[0], dh.time_to_timestamp(p[1])) for p in args.pixel])
        if args.username is not None:
            print("Getting user ids from usernames")
            user_ids += get_hash.get_hashes_by_username(args.username)

        print("Collecting data for the following user ids:")
        hash_alias = HashAliasHandler.instance()
        for user_id in user_ids:
            print(f" - {user_id} ({hash_alias.get_alias_from_hash(user_id) or 'unknown'})")

        # the individual image creators
        image_creators = {
            user_id: ImageCreator(
                background_image=args.background_image,
                background_black_white=args.background_black_white,
                background_image_opacity=args.background_image_opacity,
                background_color=args.background_color,
                output_file=self.get_filename(args, user_id)
            ) for user_id in user_ids
        }

        # TODO: only if multiple
        # combined image creator
        combined_image_creator = ImageCreator(
            background_image=args.background_image,
            background_black_white=args.background_black_white,
            background_image_opacity=args.background_image_opacity,
            background_color=args.background_color,
            output_file=self.get_filename(args)
        )

        total_pixels = 0
        user_pixels = {user_id: 0 for user_id in user_ids}

        for time, user_id, color, pixel in dh.get_data(user_ids=user_ids, include_void=args.include_void):
            total_pixels += 1

            user_pixels[user_id] += 1

            combined_image_creator.set_pixel(*[int(c) for c in pixel.split(",")], args.highlight_color or color)

            if user_id in image_creators:
                image_creators[user_id].set_pixel(*[int(c) for c in pixel.split(",")], args.highlight_color or color)

        print()
        print("-" * 8, "RESULTS", "-" * 8)
        print(f"Pixels per user:")
        print("\n".join(
            f" - {user_id} ({hash_alias.get_alias_from_hash(user_id) or 'unknown'}): {n}" for user_id, n in user_pixels.items()
        ))
        print(f"Combined number of pixels for all specified users: {total_pixels}")

        logging.info("saving images")

        combined_image_creator.save()

        for ic in image_creators.values():
            ic.save()

    def setalias(self):
        """
        Saves a given Alias
        :return:
        """

        parser = argparse.ArgumentParser(description='Saves the given Hash under the given Alias for easier queries in the future. Querying by username does this automatically.')
        parser.add_argument('hash', help="The user hash as found in the r/place data.")
        parser.add_argument('alias', help="The alias for the hash. Normally this will be the Reddit username")
        args = parser.parse_args(sys.argv[2:])

        HashAliasHandler.instance().save_alias(args.hash, args.alias)

        print(args.hash, args.alias)

    def influxdb(self):
        """
        If you wish to use the InfluxDB functionality,
        you need to execute this once before.
        This will get write all the data to the InfluxDB.
        This can take a few hours (2.5 h for me).
        """

        # get the options and set logging
        parser = argparse.ArgumentParser(description='Initialize the InfluxDB functionality by writing all data to it.')
        self.add_default_options(parser, influxdb=True)
        args = parser.parse_args(sys.argv[2:])
        self.set_logging(args.verbose)
        dh = self.init_data_handler(args)

        dh.influx_connection.initialize()


if __name__ == '__main__':
    PlaceAnalyzer()
