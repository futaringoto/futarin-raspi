from os import path
from io import BytesIO
from sys import platform
from types import FunctionType
import wave
from time import time
from sys import exit
from enum import Enum
from argparse import ArgumentParser, FileType
import tomllib
from logging import getLogger, Formatter, StreamHandler, FileHandler, Logger, DEBUG
from time import sleep
from asyncio import QueueEmpty, run, create_task, Queue
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, BinaryIO, TextIO
from websockets import connect, Data
import gpiozero
import subprocess
from pyaudio import PyAudio, get_sample_size, paInt16

### CONST ###
CONFIG_FILE_NAME = "futarin.toml"

### CLASS ###
class Processes(Enum):
    ListenMessage = 0
    TrainMessage = 1

class Signal(Enum):
    Finish = 0

class LoggerManager:
    def __init__(self) -> None:
        self.loggers = []

        self.formatter = Formatter('%(asctime)s[%(levelname)s] %(name)s - %(message)s')

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.formatter)

        self.file_handler = FileHandler(filename="futarin-raspi.log")
        self.file_handler.setLevel(DEBUG)
        self.file_handler.setFormatter(self.formatter)
        
        self.logger = self.get_logger("LoggerManager")
        self.logger.debug("initialized LoggerManager")

    def get_logger(self, name: str, console: bool = True, file: bool = True) -> Logger:
        logger = getLogger(name)
        logger.setLevel(DEBUG)
        if console:
            logger.addHandler(self.console_handler)
        if file:
            logger.addHandler(self.file_handler)
        self.loggers.append(logger)
        return logger

class Button:
    def __init__(self, pin: int, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.gpiozero_button: gpiozero.Button = gpiozero.Button(pin)
        self.logger.debug(f"Initialized Button(pin:{pin})")
    def is_pressed(self) -> bool:
        return self.gpiozero_button.value == 1
    def is_hold(self) -> bool:
        return self.gpiozero_button.value == 0
    async def wait_for_press(self) -> None:
        self.logger.debug("Start waiting for button pressed")
        self.gpiozero_button.wait_for_press() # type: ignore
        self.logger.debug("Button pressed during waiting")
        return
    async def wait_for_release(self) -> None:
        self.logger.debug("Start waiting for button released")
        self.gpiozero_button.wait_for_release() # type: ignore
        self.logger.debug("Button released during waiting")
        return

class RingLED:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        dir_name = path.dirname(__file__)
        ring_led_script_path = path.join(dir_name, "ring_led_pipe.py")
        self.ring_led_popen: subprocess.Popen = subprocess.Popen(
            ["sudo", "python3", ring_led_script_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.logger.debug("Initialized Ring LED")
    def flash(self) -> None:
        self.ring_led_popen.stdin.write(b'xyz')

class Mic:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.chunk = 1024
        self.format = paInt16
        self.channels = 1
        self.rate = 44100
        self.resetPyAudio()
        self.logger.debug("Initialized Mic")

    def resetPyAudio(self) -> None:
        self.py_audio = PyAudio()

    async def record(self, func: FunctionType) -> BytesIO:
        self.resetPyAudio() # TODO
        self.logger.debug("Start recording")
        buffer = BytesIO()
        buffer.name = f"mic-voice-{int(time())}.wav"
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(get_sample_size(self.format))
            wf.setframerate(self.rate)

            self.logger.debug("Start recording")
            stream = self.py_audio.open(format=self.format, channels=self.channels, rate=self.rate, input=True)
            while func():
                wf.writeframes(stream.read(self.chunk))
            
            stream.close()
            self.py_audio.terminate()
        
        buffer.seek(0)
        self.logger.debug("Finish recording")
        return buffer
            

            



            


class Interface:
    def __init__(self, button1_pin: int, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.logger.debug(f"Button1 Pin: {button1_pin}")
        self.button1 = Button(button1_pin, logger=self.logger)
        # self.ring_led = RingLED()
        # self.logger.debug(self.ring_led.flash())
        self.mic = Mic(logger = self.logger)
        self.logger.debug("Initialized Interface")
        
class Config:
    def __init__(self) -> None:
        self.web_dev: bool = False
        self.websocket_url: Optional[str] = None
        self.speech_send_url: Optional[str] = None
        self.button1_pin: Optional[int] = None

        config_from_args = self.get_config_from_args() #read config from args
        config_from_file = self.get_config_from_file(file = config_from_args["config_file"]) #read config from file
        self.load(config_from_file)
        self.load(config_from_args) # overwrite

    def get_config_from_args(self) -> Dict[str, Any]:
        parser = ArgumentParser()
        parser.add_argument("-d", "--web-dev", help="run as web develop mode", action="store_true")
        parser.add_argument("-f", "--config-file", help="use custom config file path", metavar="CONFIG_FILE_PATH", type=FileType('rb'), default=None)
        args = parser.parse_args()
        return vars(args)

    def get_config_from_file(self, file: Optional[BytesIO] = None) -> Dict[str, Any]:
        if file:
            return tomllib.load(file)
        else:
            script_dir = path.dirname(__file__)
            config_file_path = path.join(script_dir, CONFIG_FILE_NAME)
            with open(config_file_path, "rb") as config_file:
                return tomllib.load(config_file)

    def load(self, dict: Dict[str, Any]) -> None:
        for key in vars(self).keys():
            if key in dict:
                self.setter(key, dict[key])

    def setter(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def getter(self, key: str, value: Any) -> None:
        return getattr(self, key, value)


class WebSocket:
    def __init__(self, ws_url: str, logger :Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.ws_url = ws_url
        self.logger.debug("Initialized WebSocket")

    async def connect(self) -> None:
        self.connection = await connect(self.ws_url, open_timeout=None, ping_interval=1, logger=self.logger)
        self.logger.debug("WebSocket Connectied")

    async def send(self, value: Any) -> None:
        await self.connection.send(value)
    
    async def getReceive(self) -> Optional[Data]:
        recv = await self.connection.recv()
        if recv:
            return recv
        else:
            return None


class System:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger_manager = LoggerManager()
        # self.ws = WebSocket(self.logger_manager.get_logger("WebSocket"), self.config.websocket_url);
        self.interface = Interface(self.config.button1_pin, logger = self.logger_manager.get_logger("Interface"))
        self.logger = self.logger_manager.get_logger("System")
        self.logger.debug("Initialized Systrem")

    async def wait_for_press_button(self) -> Processes:
        await self.interface.button1.wait_for_press()
        return Processes.TrainMessage

    async def train_message(self) -> None:
        self.logger.debug("Train called") 
        file = await self.interface.mic.record(self.interface.button1.is_pressed)
        await self.playSound(file)

    async def playSound(self, file: BinaryIO) -> None:
        self.logger.debug("play sound")
        with wave.open(file, 'rb') as wf:
            p = PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            while len(data := wf.readframes(self.interface.mic.chunk)):
                self.logger.debug("play sound")
                stream.write(data)
            stream.close()
            p.terminate()

    async def listen_message(self) -> None:
        self.logger.debug("listen_message")

async def main() -> None:
    config = Config() 
    system = System(config)
    logger = system.logger_manager.get_logger("Main")

    logger.debug("start loop")
    while True:
        try:
            flag = await system.wait_for_press_button()
            if flag == Processes.TrainMessage:
                await system.train_message()
            elif flag == Processes.ListenMessage:
                await system.listen_message()
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    run(main())

