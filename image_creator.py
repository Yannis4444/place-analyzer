"""
Can create images from the collected data
"""
import logging
import os

from PIL import Image
from typing import Optional, Tuple


class ImageCreator:
    def __init__(
            self,
            background_image: Optional[str] = "resources/final_place.png",
            background_image_opacity: float = 0.1,
            background_color: str = "#000000",
            output_file: str = "place_out.png"
    ):
        """
        Initializes a new ImageCreator and sets the background to draw on later

        Set background_image to None or opacity to 0 to not show an image.

        :param background_image: An Image to show in the background (default: the final r/place canvas)
        :param background_image_opacity: The opacity of the background image (default: 0.5)
        :param background_color: The color of the canvas behind the background image.
        :param output_file: The file to save the result to.
        """

        logging.info(f"Creating image creator: {background_image}, {background_image_opacity}, {background_color}, {output_file}")

        self.background_image = background_image
        self.background_image_opacity = background_image_opacity
        self.background_color = background_color
        self.output_file = output_file

        os.makedirs(output_file.rsplit("/", 1)[0], exist_ok=True)

        self.image = Image.new("RGBA", (2000, 2000), background_color)

        if background_image is not None and background_image_opacity > 0:
            # import an image from file
            bg = Image.open(background_image)

            self.image = Image.blend(self.image, bg, background_image_opacity)

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int] | Tuple[int, int, int, int]):
        """
        Sets the color of a specified pixel
        :param x: The x coordinate
        :param y: The y coordinate
        :param color: The color as a tuple (optional alpha channel)
        """

        self.image.putpixel((x, y), color)

    def save(self):
        """
        Saves the file to the previously specified output_file
        """

        self.image.save(self.output_file, format="png")
        # self.image.show()