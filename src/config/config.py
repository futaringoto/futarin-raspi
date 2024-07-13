from os.path import exists, normpath, join, dirname
from io import BytesIO
from argparse import ArgumentParser, FileType
import tomllib
from typing import Dict, Any, Optional


class Config:
    def __init__(
        self, config_file_name: str, search_dir_path: str
    ) -> None:  # path: search config file from this path and it's parents directory
        # self.web_dev: bool = False
        self.websocket_url: Optional[str] = None
        self.speech_send_url: Optional[str] = None
        self.button1_pin: Optional[int] = None
        self.path = normpath(search_dir_path)
        self.file_name = config_file_name

        config_from_args = self.get_config_from_args()  # read config from args
        config_from_file = self.get_config_from_file(
            file=config_from_args["config_file"]
        )  # read config from file
        self.load(config_from_file)
        self.load(config_from_args)  # overwrite config when self.load is called

    def get_config_from_args(self) -> Dict[str, Any]:
        parser = ArgumentParser()
        # parser.add_argument("-d", "--web-dev", help="run as web develop mode", action="store_true")
        parser.add_argument(
            "-f",
            "--config-file",
            help="use custom config file path",
            metavar="CONFIG_FILE_PATH",
            type=FileType("rb"),
            default=None,
        )
        args = parser.parse_args()
        return vars(args)

    def get_config_from_file(self, file: Optional[BytesIO] = None) -> Dict[str, Any]:
        if file:
            return tomllib.load(file)
        else:
            search_dir = self.path
            while search_dir:
                config_file_path = join(search_dir, self.file_name)
                if exists(config_file_path):
                    with open(config_file_path, "rb") as config_file:
                        return tomllib.load(config_file)
                search_dir = None if search_dir == "/" else dirname(search_dir)
            raise FileNotFoundError("config file not found")

    def load(self, dict: Dict[str, Any]) -> None:
        for key in vars(self).keys():
            if key in dict:
                self.setter(key, dict[key])

    def setter(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def getter(self, key: str, value: Any) -> None:
        return getattr(self, key, value)
