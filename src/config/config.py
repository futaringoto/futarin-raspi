from os import getcwd
from os.path import exists, join, dirname
from argparse import ArgumentParser, FileType
import tomllib
from typing import Dict, Any, Optional, TypedDict

FILE_NAME = "futarin.toml"

Config = TypedDict(
    "Config",
    {
        "api_origin": Optional[str],
        "button_right_pin": Optional[int],
        "button_left_pin": Optional[int],
        "skip_introduction": Optional[bool],
        "api_version": Optional[int],
    },
)


def _get_config_from_args() -> Dict[str, Any]:
    parser = ArgumentParser()

    parser.add_argument(
        "-f",
        "--config-file",
        help="Set custom config file path.",
        metavar="CONFIG_FILE_PATH",
        type=FileType("rb"),
        default=None,
    )

    parser.add_argument(
        "--skip-introduction",
        help="Skip playing introduction message at startup.",
        action="store_true",
    )

    args = parser.parse_args()

    return vars(args)


def _get_config_from_file() -> Dict[str, Any]:
    file_from_args = _config_from_args["config_file"]
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


def _generate_config() -> Config:
    config = {}
    for conf in [_config_from_file, _config_from_args]:
        for key in Config.__annotations__.keys():
            if key in conf:
                config[key] = conf[key]
    return config  # type: ignore


def get(key: str) -> Any:
    return config[key]


_config_from_args = _get_config_from_args()  # read config from args
_config_from_file = _get_config_from_file()  # read config from file

config: Config = _generate_config()

if __name__ == "__main__":
    print(f"config_from_args: {_config_from_args}")
    print(f"config_from_file: {_config_from_file}")
    print(f"config: {config}")
