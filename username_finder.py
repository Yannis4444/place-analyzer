"""
Can be used to search the data provided by the Internet Archive for a user name
https://archive.org/details/place2022-opl-raw
"""
import json
import logging
import lzma
import os
from typing import List, Tuple, Optional, Dict

import requests
from tqdm import tqdm


class UsernameFinder:
    INTERNET_ARCHIVE_URL = "https://archive.org/download/place2022-opl-raw/{}"
    INTERNET_ARCHIVE_FILES = [
        "details-1648846499954.csv.xz",
        "details-1648846530849.csv.xz",
        "details-1648846617602.csv.xz",
        "details-1648846924973.csv.xz",
        "details-1648847646586.csv.xz",
        "details-1648850799528.csv.xz",
        "details-1648850852558.csv.xz",
        "details-1648851037616.csv.xz",
        "details-1648851076265.csv.xz",
        "details-1648851107891.csv.xz",
        "details-1648851186235.csv.xz",
        "details-1648851241128.csv.xz",
        "details-1648851317318.csv.xz",
        "details-1648851461813.csv.xz",
        "details-1648851871929.csv.xz",
        "details-1648851892660.csv.xz",
        "details-1648852318687.csv.xz",
        "details-1648852411672.csv.xz",
        "details-1648852464182.csv.xz",
        "details-1648852511064.csv.xz",
        "details-1648852523944.csv.xz",
        "details-1648852615620.csv.xz",
        "details-1648852723128.csv.xz",
        "details-1648852970444.csv.xz",
        "details-1648853031242.csv.xz",
        "details-1648853063579.csv.xz",
        "details-1648853162505.csv.xz",
        "details-1648853270653.csv.xz",
        "details-1648853527092.csv.xz",
        "details-1648853619041.csv.xz",
        "details-1648854129523.csv.xz",
        "details-1648854141138.csv.xz",
        "details-1648854155610.csv.xz",
        "details-1648854288198.csv.xz",
        "details-1648855986664.csv.xz",
        "details-1648856072103.csv.xz",
        "details-1648856225161.csv.xz",
        "details-1648856301087.csv.xz",
        "details-1648856756516.csv.xz",
        "details-1648856780638.csv.xz",
        "details-1648916686994.csv.xz",
        "details-1648916836150.csv.xz",
        "details-1648916935467.csv.xz",
        "details-1648916955962.csv.xz",
        "details-1648917094074.csv.xz",
        "details-1648917123519.csv.xz",
        "details-1648917297932.csv.xz",
        "details-1648917352825.csv.xz",
        "details-1648917414917.csv.xz",
        "details-1648917434118.csv.xz",
        "details-1648917503333.csv.xz",
        "details-1648918254005.csv.xz",
        "details-1648918409990.csv.xz",
        "details-1648918490475.csv.xz",
        "details-1648918654648.csv.xz",
        "details-1648918855244.csv.xz",
        "details-1648918987574.csv.xz",
        "details-1648919137613.csv.xz",
        "details-1648919143491.csv.xz",
        "details-1648919249576.csv.xz",
        "details-1648919329023.csv.xz",
        "details-1648919372640.csv.xz",
        "details-1648919391776.csv.xz",
        "details-1648919408534.csv.xz",
        "details-1648924148338.csv.xz",
        "details-1648924997299.csv.xz",
        "details-1648926051076.csv.xz",
        "details-1648926251287.csv.xz",
        "details-1648926325934.csv.xz",
        "details-1648926363072.csv.xz",
        "details-1648926662391.csv.xz",
        "details-1648926706681.csv.xz",
        "details-1648926724645.csv.xz",
        "details-1648926753057.csv.xz",
        "details-1648926763116.csv.xz",
        "details-1648926831306.csv.xz",
        "details-1648926903200.csv.xz",
        "details-1648927392699.csv.xz",
        "details-1648927436942.csv.xz",
        "details-1648927695648.csv.xz",
        "details-1648927721517.csv.xz",
        "details-1648927724975.csv.xz",
        "details-1648927749035.csv.xz",
        "details-1648927753104.csv.xz",
        "details-1648927842157.csv.xz",
        "details-1648928188597.csv.xz",
        "details-1648928217462.csv.xz",
        "details-1648928439474.csv.xz",
        "details-1648928456793.csv.xz",
        "details-1648928760261.csv.xz",
        "details-1648928832033.csv.xz",
        "details-1648928856857.csv.xz",
        "details-1648929134214.csv.xz",
        "details-1648929487533.csv.xz",
        "details-1648930345105.csv.xz",
        "details-1648930346391.csv.xz",
        "details-1648930391069.csv.xz",
        "details-1648930396540.csv.xz",
        "details-1648931370611.csv.xz",
        "details-1648932385637.csv.xz",
        "details-1648937731553.csv.xz",
        "details-1648937874674.csv.xz",
        "details-1648937919747.csv.xz",
        "details-1648937922467.csv.xz",
        "details-1648938003819.csv.xz",
        "details-1648938061222.csv.xz",
        "details-1648938090208.csv.xz",
        "details-1648940090527.csv.xz",
        "details-1648940241539.csv.xz",
        "details-1648940329389.csv.xz",
        "details-1648940479144.csv.xz",
        "details-1648940529484.csv.xz",
        "details-1648940535337.csv.xz",
        "details-1648940649165.csv.xz",
        "details-1648940698456.csv.xz",
        "details-1649013111520.csv.xz",
        "details-1649013157836.csv.xz",
        "details-1649013197899.csv.xz",
        "details-1649013222540.csv.xz",
        "details-1649013361028.csv.xz",
        "details-1649013429949.csv.xz",
        "details-1649090013255.csv.xz",
        "details-1649108974796.csv.xz"
    ]

    def __init__(self):
        """
        Creates a new username finder
        """

    def get_pixel_times(self, usernames: List[str], points_with_canvas_id: int = 3, points_without_canvas_id: int = 20) -> Dict[str, Tuple[List[Tuple[Tuple[int, int], float]], List[Tuple[Tuple[int, int], float]]]]:
        """
        Returns times and coordinates at which pixels were placed by the given users.

        Multiple points are collected for each username.
        The data sometimes doesn't include the canvas_id.
        In this case, all possible pixels are added to
        the List in the first postion of the tuple.
        Once either the number of points with a canvas id reaches points_with_canvas_id
        or the number of points without a canvas id reaches points_without_canvas_id,
        no more pixels are collected for that username.
        Note that there are four points added for each point without a canvas id.

        :param points_with_canvas_id: How many points with a canvas id are needed to consider them complete
        :param points_without_canvas_id: How many points without a canvas id are needed to consider them complete
        :return: A dictionary with usernames as keys, a tuple with a list of tuples
                 with coordinates and timestamps as values for both ones found with a canvas index and without
                 {"<username>": (
                        [  # coordinates with known canvas id
                            ((x, y), timestamp),
                            ((x, y), timestamp),
                            ((x, y), timestamp)
                        ],
                        [  # coordinates without known canvas id
                            ((x, y), timestamp),
                            ((x, y), timestamp),
                            ((x, y), timestamp),
                            ((x, y), timestamp),
                            ((x, y), timestamp),
                            ((x, y), timestamp)
                        ]
                    )
                 }
        """

        # TODO: try to get one with the canvas, only use other if none available (or if they are early enough)
        #       Maybe best of three or something like that

        os.makedirs("internet_archive_data", exist_ok=True)

        pixel_times: Dict[str, Tuple[List[Tuple[Tuple[int, int], float]], List[Tuple[Tuple[int, int], float]]]] = {
            username: (
                [],
                []
            ) for username in usernames
        }

        for filename in tqdm(self.INTERNET_ARCHIVE_FILES, desc="Searching Internet Archive", mininterval=0):
            url = self.INTERNET_ARCHIVE_URL.format(filename)

            path = f"internet_archive_data/{filename}"

            # skip if the file already exists
            if not os.path.isfile(path):
                logging.info(f"Downloading {url}")

                try:
                    file = requests.get(url, allow_redirects=True)
                    with open(path, 'wb') as f:
                        f.write(file.content)

                except Exception as e:
                    logging.error(f"Failed to download {url}")
                    logging.exception(e)
                    exit(-1)

            with lzma.open(path) as file:
                for line in file:
                    t, _, _, data = line.decode().split(",", 3)

                    data = data[1:-2].replace("\\\"", "\"").replace("\\n", "")

                    json_data = json.loads(data)

                    if data is None:
                        continue

                    if "data" in json_data and json_data["data"] is not None:
                        for pixel, pixel_data in json_data["data"].items():
                            try:
                                canvas: Optional[int] = None
                                if "c" in pixel:
                                    # the canvas is included
                                    pixel, canvas_raw = pixel.split("c")
                                    canvas = int(canvas_raw)
                                # TODO: If the point was before the first expansion, add id 0

                                x, y = (int(c) for c in pixel.replace("p", "").split("x"))

                                if canvas is not None:
                                    if canvas in [1, 3]:
                                        x += 1000
                                    if canvas in [2, 3]:
                                        y += 1000

                                if "data" in pixel_data and pixel_data["data"] is not None:
                                    for user_data in pixel_data["data"]:
                                        if "data" in user_data and user_data["data"] is not None and "lastModifiedTimestamp" in user_data["data"] and user_data["data"]["lastModifiedTimestamp"] is not None and "userInfo" in user_data["data"] and user_data["data"]["userInfo"] is not None and "username" in user_data["data"]["userInfo"] and user_data["data"]["userInfo"]["username"] is not None:
                                            pixel_time = user_data["data"]["lastModifiedTimestamp"] / 1000
                                            username = user_data["data"]["userInfo"]["username"]

                                            if username in usernames:
                                                logging.info(f"Found {username} in {filename}: ({x},{y}) at {pixel_time}")

                                                if canvas is None:
                                                    # no canvas ID -> add all four
                                                    pixel_times[username][1].append(((x, y), pixel_time))
                                                    pixel_times[username][1].append(((x, y + 1000), pixel_time))
                                                    pixel_times[username][1].append(((x + 1000, y), pixel_time))
                                                    pixel_times[username][1].append(((x + 1000, y + 1000), pixel_time))
                                                else:
                                                    # canvas ID is known
                                                    pixel_times[username][0].append(((x, y), pixel_time))

                                                if len(pixel_times[username][0]) >= points_with_canvas_id or len(pixel_times[username][1]) >= points_without_canvas_id:
                                                    usernames.remove(username)

                                                if not usernames:
                                                    return pixel_times

                            except Exception as e:
                                logging.debug(f"Could not get pixel information from {pixel_data}: {e}")

        return pixel_times
