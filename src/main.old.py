from collections.abc import Coroutine
from os import path
from enum import Enum
import argparse
import tomllib
import logging
from time import sleep
import asyncio
from abc import ABC, abstractmethod
from typing import Literal
import websockets
from gpiozero import Button


### CONST ###
CONFIG_FILE_NAME = "futarin.toml"

### logging ###
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(filename="futarin-raspi.log")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


### main ###
async def main():
    ## get config ##
    config = generate_config()
    logger.debug(vars(config))
    
    ws = WSManger(config.websocket_url)
    await ws.connect()
        



## CLASS ###
class Config:
    def __init__(self):
        #default config
        self.web_dev = False
        self.websocket_url = None
        self.speech_post_url = None

    def load(self, dict):
        for key in vars(self).keys():
            if key in dict:
                self.setter(key, dict[key])

    def setter(self, key, value):
        setattr(self, key, value)

    def getter(self, key, value):
        return getattr(self, key, value)

class Status:
    def __init__(self):
        self.mode = Modes.Disconnected
    
    def setter(self, key, value):
        setattr(self, key, value)

    def getter(self, key, value):
        return getattr(self, key, value)

class WSManger:
    def __init__(self, ws_url):
        self.ws_url = ws_url        

    async def connect(self):
        self.connection = await websockets.connect(self.ws_url, open_timeout=None, ping_interval=1, logger=logger)

    async def send(self, value):
        await self.connection.send(value)
    
    async def getReceive(self):
        recv = await self.connection.recv()
        if recv:
            return recv
        else:
            return None

class ButtonABC(ABC):
    @abstractmethod 
    def __init__(self):
        pass

    @abstractmethod 
    async def wait_for_press(self, timeout=None) -> Coroutine[Any, Any, Literal[True] | None]:
        return

class WebButtonManger(ButtonABC):
    def __init__(self, pin):
        self.pin = pin
    
    async def wait_for_press(self, timeout=None):
        return True 
        return None

class ButtonManger(ButtonABC):
    def __init__(self, pin):
        self.button = Button(pin)

    async def wait_for_press(self, timeout=None):
        if timeout:
            try:
                await asyncio.wait_for(self.button.wait_for_press(), timeout=timeout)
            except asyncio.TimeoutError:
                return None
        else:
            self.button.wait_for_press()
        return True

class Modes(Enum):
    Disconnected = 0
    Connecting = 100
    Sleeping = 200
    AwaitLisningMessage = 301
    Recording = 300
    GenelatingAdvice = 301
    PlayingAdvice = 302
    PlayingMessage = 403
    AwaitNadenade = 404
  

### config ###
def generate_config():
    config_from_args = get_config_from_args() #read config from args
    config_from_file = get_config_from_file(config_from_args["config_file"]) #read config from file
    ### Create Config ###
    config = Config()
    config.load(config_from_file)
    config.load(config_from_args) # overwrite
    return config

def get_config_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--web-dev", help="run as web develop mode", action="store_true")
    parser.add_argument("-f", "--config-file", help="use custom config file path", metavar="CONFIG_FILE_PATH", type=argparse.FileType('rb'), default=None)
    args = parser.parse_args()
    return vars(args)

def get_config_from_file(file_from_args):
    if file_from_args:
        return tomllib.load(file_from_args)
    else:
        script_dir = path.dirname(__file__)
        config_file_path = path.join(script_dir, CONFIG_FILE_NAME)
        config_from_file = {}
        with open(config_file_path, "rb") as config_file:
            return tomllib.load(config_file)



if __name__ == "__main__":
    asyncio.run(main())

    
