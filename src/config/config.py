from typing import (
    Callable,
    Iterable,
    Optional,
    TypeVar,
    Dict,
    Generic,
    Type,
    Any,
    TypedDict,
    List,
    NotRequired,
    IO,
)
from argparse import (
    ArgumentParser,
    Action,
    FileType,
)
import tomllib
from os import getcwd, path
from src.log.log import log

FILE_NAME = "futarin.toml"


T = TypeVar("T")


class ArgparseOptions(TypedDict, Generic[T]):
    name_or_flugs: List[str]
    action: NotRequired[str | type[Action]]
    nargs: NotRequired[int | str]
    const: NotRequired[Any]
    type: NotRequired[int | float | FileType | Callable]
    choices: NotRequired[Iterable]
    required: NotRequired[bool]
    metavar: NotRequired[str | tuple[str, ...]]


class Prop(TypedDict, Generic[T]):
    name: str
    value: NotRequired[T]
    type: Type[T]
    help: str
    default: NotRequired[T]
    argparse_options: NotRequired[ArgparseOptions]


Config = Dict[str, Prop]


class ConfigNotSetError(Exception):
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return f"{self.key} has not been set"


def add_prop(prop: Prop):
    config[prop["name"]] = prop


def get_arg_parser(config: Config) -> ArgumentParser:
    parser = ArgumentParser()
    for prop in config.values():
        if "argparse_options" in prop:
            kwargs = {
                k: v
                for k, v in {**prop, **prop["argparse_options"]}.items()
                if k
                in [
                    "action",
                    "nargs",
                    "const",
                    "type",
                    "choices",
                    "required",
                    "help",
                    "metavar",
                ]
            }
            if "action" in kwargs and "type" in kwargs:
                kwargs.pop("type")
            kwargs["dest"] = prop["name"]
            parser.add_argument(
                *prop["argparse_options"]["name_or_flugs"],
                **kwargs,
            )
    return parser


def get_config_from_file(file: Optional[IO] = None):
    if file:
        return tomllib.load(file)
    else:
        search_dir = getcwd()
        while search_dir:
            config_file_path = path.join(search_dir, FILE_NAME)
            if path.exists(config_file_path):
                with open(config_file_path, "rb") as config_file:
                    return tomllib.load(config_file)
            search_dir = None if search_dir == "/" else path.dirname(search_dir)
        raise FileNotFoundError("config file not found")


def get(*keys: str, **keys_with_default: Any) -> Any:
    if len(keys) == 1:
        key = keys[0]
        if key in config:
            prop = config[key]
            if "value" in prop:
                return prop["value"]
            elif "default" in prop:
                return prop["default"]
            else:
                raise ConfigNotSetError(key)
        else:
            raise KeyError(f"{key} is not found from config")
    elif len(keys_with_default) == 1:
        key, value = next(iter(keys_with_default))
        if key in config:
            prop = config[key]
            if "value" in prop:
                return prop["value"]
            elif "default" in prop:
                return prop["default"]
            else:
                return value
        else:
            raise KeyError(f"{key} is not found from config")
    else:
        args_count = len(keys) + len(keys_with_default)
        raise TypeError(
            f"get() takes 1 position or keyword argument but {args_count} were given"
        )


def get_multiple(*keys: str, **keys_with_default: Any) -> tuple:
    result: List[Any] = []
    for key in keys:
        if key in config:
            prop: Prop = config[key]
            if "value" in prop:
                result.append(prop["value"])
            elif "default" in prop:
                result.append(prop["default"])
            else:
                raise ConfigNotSetError(key)
        else:
            raise KeyError(f"{key} is not found from config")

    for key, value in keys_with_default.items():
        if key in config:
            prop: Prop = config[key]
            if "value" in prop:
                result.append(prop["value"])
            elif "default" in prop:
                result.append(prop["default"])
            else:
                result.append(value)
        else:
            raise KeyError(f"{key} is not found from config")

    return tuple(result)


logger = log.get_logger("Config")

config: Config = {}
add_prop({"name": "api_origin", "type": str, "help": "Backend API origin"})
add_prop(
    {
        "name": "id",
        "type": int,
        "help": "futarin id",
    }
)
add_prop(
    {
        "name": "led_server_origin",
        "type": str,
        "help": "futarin-led server origin",
        "default": "http://127.0.0.1:8080",
    }
)
add_prop(
    {
        "name": "input_audio_device_name",
        "type": str,
        "help": "Input audio device(Microphone) name",
        "default": "BY Y02",
    }
)
add_prop(
    {
        "name": "output_audio_device_name",
        "type": str,
        "help": "Output audio device(Speaker) name",
        "default": "BY Y02",
    }
)
add_prop(
    {
        "name": "main_button_pin",
        "type": int,
        "help": "Main button pin number",
        "default": 18,
    }
)
add_prop(
    {
        "name": "sub_button_pin",
        "type": int,
        "help": "Sub button pin number",
        "default": 24,
    }
)
add_prop(
    {
        "name": "delta_volume",
        "type": int,
        "help": "Delta Volume(decibel) (Default volume - this)",
        "default": 0,
    }
)
add_prop(
    {
        "name": "skip_introduction",
        "type": bool,
        "help": "Skip playing introduction message at startup",
        "default": False,
        "argparse_options": {
            "name_or_flugs": ["--skip-intro"],
            "action": "store_true",
        },
    }
)
add_prop(
    {
        "name": "config_file",
        "type": str,
        "help": "Config file path(must be TOML)",
        "argparse_options": {
            "name_or_flugs": ["--config-file"],
            "metavar": "CONFIG_FILE_PATH",
            "type": FileType("rb"),
        },
    }
)

arg_parser = get_arg_parser(config)
config_from_args = vars(arg_parser.parse_args())
config_from_file = get_config_from_file(config_from_args.get("config_file"))

for key, value in (config_from_file | config_from_args).items():
    if key in config:
        config[key]["value"] = value
    else:
        logger.warn(f"{key} is not found from config")

logger.info("Initialized.")

if __name__ == "__main__":
    print(f"{config_from_args=}")
    print(f"{config_from_file=}")
    print(f"{config=}")
