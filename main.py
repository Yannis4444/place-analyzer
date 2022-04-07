__version__ = "1.0.0"
__author__ = 'Yannis Vierkoetter'

import argparse
import logging

from data_handler import DataHandler


def get_args() -> argparse.Namespace:
    """
    Gets all commandline arguments and validates them.

    :return: The arguments
    """

    parser = argparse.ArgumentParser(description='A script that can analyze different aspects from r/place and create statistics for users or communities.')
    parser.add_argument('--version', required=False, action='count', default=0, help="Print the Version")
    parser.add_argument('-v', '--verbose', required=False, action='count', default=0, help="Enable verbose output")

    args = parser.parse_args()

    if args.version:
        print(__version__)
        exit(0)

    return args


if __name__ == '__main__':
    args = get_args()

    # set logging level
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s',
    )

    # set the args in other parts
    DataHandler.instance().set_args(args)

    DataHandler.instance().download_data()
