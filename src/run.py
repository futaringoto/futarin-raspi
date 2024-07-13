import wave
from sys import exit
from enum import Enum
from logging import getLogger, Logger
from asyncio import run
from typing import Optional, BinaryIO
from pyaudio import PyAudio

from src.config.config import Config
from src.interface.button import Button
from src.interface.mic import Mic
from src.log.logger import LoggerManager

### CONST ###
CONFIG_FILE_NAME = "futarin.toml"


### CLASS ###
class Processes(Enum):
    ListenMessage = 0
    TrainMessage = 1


## Interface ##
class Interface:
    def __init__(self, button1_pin: int, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.logger.debug(f"Button1 Pin: {button1_pin}")
        self.button1 = Button(button1_pin, logger=self.logger)
        # self.ring_led = RingLED()
        # self.logger.debug(self.ring_led.flash())
        self.mic = Mic(logger=self.logger)
        self.logger.debug("Initialized Interface")


class System:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger_manager = LoggerManager()
        # self.ws = WebSocket(self.logger_manager.get_logger("WebSocket"), self.config.websocket_url);
        self.interface = Interface(
            self.config.button1_pin, logger=self.logger_manager.get_logger("Interface")
        )
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
        with wave.open(file, "rb") as wf:
            p = PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )
            while len(data := wf.readframes(self.interface.mic.chunk)):
                self.logger.debug("play sound")
                stream.write(data)
            stream.close()
            p.terminate()

    async def listen_message(self) -> None:
        self.logger.debug("listen_message")


async def main() -> None:
    config = Config(CONFIG_FILE_NAME, __file__)
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
