import argparse
import logging
import sys
from typing import List, Optional, Dict

import get_hash
import validations
from data_handler import DataHandler
from image_creator import ImageCreator


class PlaceAnalyzer:
    def __init__(self):
        """
        Gets all commandline arguments and validates them.

        :return: The arguments
        """

        # TODO: consistent naming of hash and user id

        parser = argparse.ArgumentParser(
            description='A script that can analyze different aspects from r/place and create statistics for users or communities.',
            usage=f"""{sys.argv[0]} <command> [OPTIONS]

Commands:
  gethash [OPTIONS] Get the hashed identifier of a user
                    as used in the data using a known pixel.
  user [OPTIONS]    Analyze the activity of a user (or a
                    group of users).
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
        self.init_data_handler(args)

        # get the hash for the user
        print(get_hash.get_hash(args.pixel, args.time))

    def user(self):
        """
        Analyze the activity of a user (or a
        group of users).
        """

        # get the options and set logging
        parser = argparse.ArgumentParser(description='Analyzes the activity of the specified users. Users can be specified using their user-id/hash (see gethash command) or using a known pixel just like gethash.')
        parser.add_argument('-u', '--user-id', required=False, type=str, action="append", help="The user-id/hash of a user to include", metavar="<user>")
        parser.add_argument('-p', '--pixel', required=False, type=validations.validate_pixel_time, action="append", help="A known pixel and time to automatically get the user like gethash. x,y-hh:mm (example: \"420,69-69:42\").", metavar="<pixel>")
        parser.add_argument('-d', '--include-void', required=False, action='count', default=0, help="Include The pixels placed as a part of the white void at the end.")
        parser.add_argument('-o', '--output', required=False, type=str, help="A filename for the generated png image. The user id will be appended to the name if the data is not combined.", default="out/user_canvas.png")
        parser.add_argument('-i', '--individual', required=False, action='count', default=0, help="Generate individual canvases for the given users.")
        parser.add_argument('-c', '--combine', required=False, action='count', default=0, help="Combine the given users into one image.")
        parser.add_argument('-b', '--background-image', required=False, type=str, help="The image to use as the background.", default="resources/final_place.png", metavar="<file>")
        parser.add_argument('-a', '--background-image-opacity', required=False, type=float, help="The opacity of the background image.", default=0.1, metavar="<value>")
        parser.add_argument('-l', '--background-color', required=False, type=str, help="The color for the background.", default="#000000", metavar="<color>")
        parser.add_argument('-g', '--highlight-color', required=False, type=str, help="The color for the highlighted pixels. The color of the placed pixel is used if not specified", metavar="<color>")
        self.add_default_options(parser)
        args = parser.parse_args(sys.argv[2:])
        self.set_logging(args.verbose)
        dh = self.init_data_handler(args)

        # temporary data check
        # last_time = -1
        # for i, df in enumerate(dh.get_data_frames()):
        #     for row in df[["time"]].itertuples():
        #         t = int(row[1])
        #     # for row in pd.concat([df[["time"]].head(1), df[["time"]].tail(1)]).itertuples():
        #         if not last_time <= t:
        #             print(i, "FUCK", last_time, t)
        #         # else:
        #         #     print(i, "YAY ", last_time, t)
        #         last_time = t
        # exit()

        # get all hashes to be used
        user_ids: List[str] = args.user_id or []
        if args.pixel is not None:
            print("Getting user ids from known pixels")
            user_ids += get_hash.get_hashes(args.pixel)

        print("Collecting data for the following user ids:")
        for user_id in user_ids:
            print(f" - {user_id}")

        # TODO: weight for users -> Then this can be used for other stuff as well

        # the individual image creators
        image_creators: Optional[Dict[str, ImageCreator]] = None
        if args.individual:
            image_creators = {
                user_id: ImageCreator(
                    background_image=args.background_image,
                    background_image_opacity=args.background_image_opacity,
                    background_color=args.background_color,
                    output_file="{}_{}.{}".format(args.output.rsplit(".", 1)[0], user_id, args.output.rsplit(".", 1)[1])
                ) for user_id in user_ids
            }

        combined_image_creator: Optional[ImageCreator] = None
        if args.combine:
            combined_image_creator = ImageCreator(
                background_image=args.background_image,
                background_image_opacity=args.background_image_opacity,
                background_color=args.background_color,
                output_file="{}_combined.{}".format(*args.output.rsplit(".", 1))
            )

        total_pixels = 0
        user_pixels = {user_id: 0 for user_id in user_ids}
        for df in dh.get_data_frames(user_ids=user_ids):
            total_pixels += len(df)

            for row in df[["user_id", "pixel_color", "coordinate"]].itertuples():
                user_id = str(row[1])
                color = args.highlight_color or str(row[2])
                pixel = str(row[3])

                user_pixels[user_id] += 1

                if args.combine:
                    combined_image_creator.set_pixel(*[int(c) for c in pixel.split(",")], color)

                if args.individual and user_id in image_creators:
                    image_creators[user_id].set_pixel(*[int(c) for c in pixel.split(",")], color)

        print("-"*20)
        print(f"Pixels per user:")
        print("\n".join(
            f" - {user_id}: {n}" for user_id, n in user_pixels.items()
        ))
        print(f"Combined number of pixels for all specified users: {total_pixels}")

        logging.info("saving images")

        if args.combine:
            combined_image_creator.save()

        if args.individual:
            for ic in image_creators.values():
                ic.save()

if __name__ == '__main__':
    PlaceAnalyzer()
