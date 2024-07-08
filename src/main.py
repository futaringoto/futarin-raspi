from os import path
from enum import Enum
import argparse
import tomllib
import logging
from time import sleep
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import websockets
import gpiozero
import subprocess

### CONST ###
CONFIG_FILE_NAME = "futarin.toml"

### CLASS ###
class Processes(Enum):
    ListenMessage = 0
    TrainMessage = 1

class LoggerManager:
    def __init__(self):
        self.loggers = []

        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)
        self.console_handler.setFormatter(self.formatter)

        self.file_handler = logging.FileHandler(filename="futarin-raspi.log")
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)

    def get_logger(self, name, console=True, file=True) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        if console:
            logger.addHandler(self.console_handler)
        if file:
            logger.addHandler(self.file_handler)
        self.loggers.append(logger)
        return logger

class Button:
    def __init__(self, pin) -> None:
        self.gpiozero_button: gpiozero.Button = gpiozero.Button(pin)
    def is_pressed(self) -> bool:
        return self.gpiozero_button.value == 1
    def is_hold(self) -> bool:
        return self.gpiozero_button.value == 0

class RingLED:
    def __init__(self) -> None:
        dir_name = path.dirname(__file__)
        ring_led_script_path = path.join(dir_name, "ring_led_pipe.py")
        self.ring_led_pipe = subprocess.Popen(
            ["sudo", "python3", ring_led_script_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    def flash(self):
        self.ring_led_pipe.stdin.write(b'xyz')

class Mic:
    pass

class WebVirtualInterface:
    pass

class Interface:
    def __init__(self, state) -> None:
        self.logger = state.logger_manager.get_logger("Interface")
        if state.config.web_dev == False:
            #self.button = Button(state.config.button_pin)
            self.ring_led = RingLED()
            self.logger.debug(self.ring_led.flash())
            # self.mic = Mic()
        else:
            self.virtual_interface = WebVirtualInterface()
            self.button = self.virtual_interface.button()
            self.ring_led = self.virtual_interface.ring_led()
            self.mic = self.virtual_interface.mic()

class State:
    def __init__(self) -> None:
        self.config = generate_config() 

        self.logger_manager = LoggerManager()
        self.interface = Interface(self)
        self.ws = WebSocketDaemon(self, self.config.websocket_url)

class Wait:
    def __init__(self, state) -> None:
        self.logger = state.logger_manager.get_logger("Wait")
    async def wait_for_button(self) -> Dict[str, Processes]:
        self.logger.debug("Wait called")
        sleep(3)
        return {"nextProcess": Processes.TrainMessage}

class TrainMessage:
    def __init__(self, state) -> None:
        self.logger = state.logger_manager.get_logger("TrainMessage")
    async def run(self):
        self.logger.debug("Train called") 

class ListenMessage:
    def __init__(self, state) -> None:
        self.logger = state.logger_manager.get_logger("ListenMessage")
    async def run(self):
        self.logger.debug("Listen called")
        
class Config:
    def __init__(self):
        #default config
        self.web_dev = False
        self.websocket_url = None
        self.speech_send_url = None
        self.button_pin = None

    def load(self, dict):
        for key in vars(self).keys():
            if key in dict:
                self.setter(key, dict[key])

    def setter(self, key, value):
        setattr(self, key, value)

    def getter(self, key, value):
        return getattr(self, key, value)


class WebSocketDaemon:
    def __init__(self, state, ws_url):
        self.ws_url = ws_url
        self.logger = state.logger_manager.get_logger("WebSocketDaemon")

    async def connect(self):
        self.connection = await websockets.connect(self.ws_url, open_timeout=None, ping_interval=1, logger=self.logger)

    async def send(self, value):
        await self.connection.send(value)
    
    async def wait_for_receive(self):
        recv = await self.connection.recv()
        return recv


### Functions ###

async def init() -> State:
    state = State()
    await state.ws.connect()
    return state

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
        with open(config_file_path, "rb") as config_file:
            return tomllib.load(config_file)


async def main():
    state = await init()
    logger = state.logger_manager.get_logger("Main")
    # logger = state.logger_manager.get_logger("main")
    wait = Wait(state)
    train_message = TrainMessage(state)
    listen_message = ListenMessage(state)

    logger.debug("start loop")
    while True:
        try:
            flag = await wait.wait_for_button()
            if flag["nextProcess"] == Processes.TrainMessage:
                await train_message.run()
            elif flag["nextProcess"] == Processes.ListenMessage:
                await listen_message.run()
        except KeyboardInterrupt:
            return            
        except Exception as e:
            logger.error(e)
            return



if __name__ == "__main__":
    asyncio.run(main())

    
