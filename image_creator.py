"""
Can create images from the collected data
"""
import logging
import os

from PIL import Image
from typing import Optional, Tuple

from data_handler import DataHandler


class ImageCreator:
    def __init__(
            self,
            background_image: Optional[str] = "resources/final_place.png",
            background_black_white: bool = False,
            background_image_opacity: float = 0.1,
            background_color: str = "#000000",
            output_file: str = "place_out.png",
            gif_length: Optional[int] = None,
            gif_fps=5
    ):
        """
        Initializes a new ImageCreator and sets the background to draw on later

        Set background_image to None or opacity to 0 to not show an image.

        If a gif_length is given, a gif will be created as well.
        The last 10% of the image will be a still image.

        :param background_image: An Image to show in the background (default: the final r/place canvas)
        :param background_image_opacity: The opacity of the background image (default: 0.5)
        :param background_color: The color of the canvas behind the background image.
        :param output_file: The file to save the result to.
        :param gif_length: If set, a gif with the given length is created.
        :param gif_fps: Approximate fps for the gif.
        """

        logging.info(f"Creating image creator: {background_image}, {background_image_opacity}, {background_color}, {output_file}")

        self.background_image = background_image
        self.background_black_white = background_black_white
        self.background_image_opacity = background_image_opacity
        self.background_color = background_color
        self.output_file = output_file
        self.gif_length = gif_length
        self.gif_fps = gif_fps

        os.makedirs(output_file.rsplit("/", 1)[0], exist_ok=True)

        self.image = Image.new("RGBA", (2000, 2000), background_color)

        if background_image is not None and background_image_opacity > 0:
            # import an image from file
            bg: Image.Image = Image.open(background_image)

            if background_black_white:
                bg = bg.convert("LA")
                bg = bg.convert(self.image.mode)

            self.image = Image.blend(self.image, bg, background_image_opacity)

        # gif stuff
        if gif_length is not None:
            total_images = gif_fps * gif_length
            self.gif_n_images = round(total_images * 0.9)
            self.gif_n_still_image = total_images - self.gif_n_images
            # all the images under their index
            # if one is empty in the end, the one before will be used
            self.gif_images: dict = {
                i: None for i in range(self.gif_n_images)
            }
            self.gif_images[0] = self.image.copy()
            self.gif_last_image_index = 0

            dh = DataHandler.instance()
            self.gif_start_timestamp = dh.start_time
            self.gif_end_timestamp = dh.end_time

    def hex_to_rgb(self, hex_color) -> Tuple[int, int, int]:
        """
        Converts a hex color (without alpha channel) to a tuple

        :param hex_color: The hex color
        :return: The tuple
        """

        return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))

    def set_pixel(self, x: int, y: int, color, timestamp: float):
        """
        Sets the color of a specified pixel
        :param x: The x coordinate
        :param y: The y coordinate
        :param color: The color as a tuple (optional alpha channel) or string
        :param timestamp: The timestamp of the pixel
        """

        # save last image to the gif images if this is not for the same frame
        if self.gif_length is not None:
            index = int(min((timestamp - self.gif_start_timestamp) / (self.gif_end_timestamp - self.gif_start_timestamp), 1) * self.gif_n_images)

            if index != self.gif_last_image_index:
                self.gif_images[self.gif_last_image_index] = self.image.copy()
                self.gif_last_image_index = index

        if type(color) == str:
            color = self.hex_to_rgb(color)

        self.image.putpixel((x, y), color)

    def save(self):
        """
        Saves the file to the previously specified output_file
        """

        logging.info(f"Saving {self.output_file}")
        self.image.save(self.output_file, format="png")
        # self.image.show()

        # save the gif
        if self.gif_length is not None:
            filename = self.output_file.replace(".png", ".gif")
            logging.info(f"Saving {filename}")

            self.gif_images[self.gif_last_image_index] = self.image

            images = []
            for i, image in self.gif_images.items():
                if image is not None:
                    images.append(image.convert("RGB"))
                else:
                    images.append(images[-1].copy())

            for i in range(self.gif_n_still_image):
                images.append(images[-1].copy())

            images[0].save(filename,
                           save_all=True, append_images=images[1:],
                           optimize=False, duration=self.gif_length, loop=True)
