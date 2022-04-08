import argparse
import logging
import sys

import get_hash
import validations
from data_handler import DataHandler


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
    gethash [OPTIONS]   Get the hashed identifier of a user
                        as used in the data using a known pixel.
""")

        parser.add_argument('command', help="Command to run")

        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def add_default_options(self, parser: argparse.ArgumentParser):
        """
        Adds default arguments to a parser like verbose

        :param parser: The parser to add the options to
        """

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
        parser.add_argument('-p', '--pixel', required=True, type=validations.validate_pixel, help="The comma seperated coordinates of the pixel (example: \"420,69\").", metavar="<pixel>")
        parser.add_argument('-t', '--time', required=True, type=validations.validate_time, help="Some time at which the pixel was last set by the desired user (example: \"69:42\").", metavar="<time>")
        self.add_default_options(parser)
        args = parser.parse_args(sys.argv[2:])
        self.set_logging(args.verbose)
        dh = self.init_data_handler(args)

        print(get_hash.get_hash(args.pixel, args.time))

        # print(args.pixel)
        # print(args.time)

        # set the args in other parts

        # for df in dh.get_data_frames():
        #     print(df)


if __name__ == '__main__':
    PlaceAnalyzer()
