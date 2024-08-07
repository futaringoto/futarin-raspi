from os import getcwd
from os.path import exists, join, dirname
from argparse import ArgumentParser, FileType
import tomllib
from typing import Dict, Any, Optional, TypedDict

FILE_NAME = "futarin.toml"
Config = TypedDict(
    "Config",
    {
        "api_endpoint_url": Optional[str],
        "button_right_pin": Optional[int],
        "button_left_pin": Optional[int],
        "skip_welcome_msg": Optional[bool],
    },
)


def get_config_from_args() -> Dict[str, Any]:
    parser = ArgumentParser()
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


def get_config_from_file() -> Dict[str, Any]:
    file_from_args = config_from_args["config_file"]
    if file_from_args:
        return tomllib.load(file_from_args)
    else:
        search_dir = getcwd()
        while search_dir:
            config_file_path = join(search_dir, FILE_NAME)
            if exists(config_file_path):
                with open(config_file_path, "rb") as config_file:
                    return tomllib.load(config_file)
            search_dir = None if search_dir == "/" else dirname(search_dir)
        raise FileNotFoundError("config file not found")


def generate_config() -> Config:
    config = {}
    for conf in [config_from_file, config_from_args]:
        for key in Config.__annotations__.keys():
            if key in conf:
                config[key] = conf[key]
    return config  # type: ignore


def get(key: str) -> Any:
    return config[key]


config_from_args = get_config_from_args()  # read config from args
config_from_file = get_config_from_file()  # read config from file

config: Config = generate_config()

if __name__ == "__main__":
    print(f"config_from_args: {config_from_args}")
    print(f"config_from_file: {config_from_file}")
    print(f"config: {config}")
