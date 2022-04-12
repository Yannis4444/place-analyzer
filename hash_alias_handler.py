"""
Used to save aliases for user hashes.
When getting a username for example this is automatically set to the username.
Also used for getting usernames that were previously gotten
"""

import logging
import configparser
import os
import threading
from typing import Optional


class HashAliasHandler:
    _singleton_lock = threading.Lock()
    _instance: 'DataHandler' = None

    @classmethod
    def instance(cls) -> 'HashAliasHandler':
        """
        Returns the hash alias handler singleton

        :return: The data handler instance
        """

        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """
        Creates a new hash alias handler.
        This should not be called directly as this is a singleton.

        :raises RuntimeError if called directly a second time
        """

        if self._instance is not None:
            raise RuntimeError(f"{self.__name__} is a singleton")
        else:
            self._instance = self

        self.directory = "."
        self.file = os.path.join(self.directory, "hash_aliases.ini")

        self.config = configparser.ConfigParser()

        # disable making keys lower case
        self.config.optionxform = str

        self._read()

    def _read(self):
        """
        Loads the config from file.
        If the file does not exist, default values will be set.
        """

        logging.info("Reading config file: {}".format(self.file))

        # get the actual values
        self.config.read(self.file)

        if not self.config.has_section("ALIASES"):
            self.config.add_section("ALIASES")
            self.save()

    def save_alias(self, hash: str, alias: str):
        """
        Saves a new alias for a given hash.

        :param hash: The user hash
        :param alias: The alias
        """

        logging.info(f"Saving alias {alias} for {hash}")

        self.config.set("ALIASES", alias, hash)

        self.save()

    def get_hash_from_alias(self, alias: str) -> Optional[str]:
        """
        Gets the hash for a given alias from the saved config

        :param alias: The alias
        :return: The hash if available
        """

        return self.config.get("ALIASES", alias, fallback=None)

    def get_alias_from_hash(self, hash: str) -> Optional[str]:
        """
        Gets the alias for a given hash from the saved config

        :param hash: The hash
        :return: The alias if available
        """

        for alias, h in dict(self.config.items('ALIASES')).items():
            if h == hash:
                return alias

    def save(self):
        """
        Saves the config to.
        """

        os.makedirs(self.directory, exist_ok=True)

        with open(self.file, 'w') as configfile:
            self.config.write(configfile)
