from io import BytesIO
from os import PathLike
import wave
from sys import exit
from enum import Enum
from logging import getLogger, Logger
import asyncio
from typing import Optional, BinaryIO
from pyaudio import PyAudio
from httpx import stream, codes
import subprocess
from pydub import AudioSegment

from src.config.config import Config
from src.interface.button import Button
from src.interface.mic import Mic
from src.log.logger import LoggerManager

### CONST ###
CONFIG_FILE_NAME = "futarin.toml"
WELLCOME_MESSAGE_PATH: PathLike[str] = "assets/audio/wellcome.wav"  # type: ignore
PLEASE_WAIT_MESSAGE_PATH: PathLike[str] = "assets/audio/please_wait.wav"  # type: ignore
FAIL_MESSAGE_PATH: PathLike[str] = "assets/audio/fail.wav"  # type: ignore
WHAT_HAPPEN_PATH: PathLike[str] = "assets/audio/whathappen.wav"  # type: ignore
# CONNECTING_MESSAGE_PATH: PathLike[str] = "assets/audio/connecting.wav"  # type: ignore
# CONNECTED_MESSAGE_PATH: PathLike[str] = "assets/audio/connected.wav"  # type: ignore
# PING_INTERVAL_SEC: int = 4


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
            self.config.button1_pin,  # type: ignore
            logger=self.logger_manager.get_logger("Interface"),  # type: ignore
        )
        self.logger = self.logger_manager.get_logger("System")
        self.logger.debug("Initialized Systrem")

    async def wait_for_press_button(self) -> Processes:
        await self.interface.button1.wait_for_press()
        self.logger.debug("Button Pressed")
        return Processes.TrainMessage

    async def train_message(self) -> None:
        self.logger.debug("Train called")
        whathappen = await self.load_buffer_file(WHAT_HAPPEN_PATH)
        await self.play_sound(whathappen)
        file = await self.interface.mic.record(self.interface.button1.is_pressed)  # type: ignore
        backend_task = asyncio.create_task(self.call_backend(file))
        audio_file = await self.load_buffer_file(PLEASE_WAIT_MESSAGE_PATH)
        await self.play_sound(audio_file)
        processed_file = await backend_task
        if processed_file:
            await self.play_sound(processed_file)
        else:
            fail_msg = await self.load_buffer_file(FAIL_MESSAGE_PATH)
            await self.play_sound(fail_msg)

    async def play_sound(self, file: BinaryIO) -> None:
        self.logger.debug("play sound")
        RATE = 44100
        processed_file = BytesIO()
        with wave.open(file, "rb") as wf:
            audio = AudioSegment.from_raw(
                file,
                sample_width=wf.getsampwidth(),
                frame_rate=wf.getframerate(),
                channels=wf.getnchannels(),
            )
            audio = audio.set_frame_rate(RATE)
            processed_file = audio.export(processed_file, format="wav")

        with wave.open(processed_file, "rb") as wf:
            p = PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=1,
            )

            self.logger.debug("start playing sound")
            while len(data := wf.readframes(self.interface.mic.chunk)):
                stream.write(data)
            stream.close()
            p.terminate()
            self.logger.debug("finish playing sound")

    async def listen_message(self) -> None:
        self.logger.debug("listen_message")

    async def call_backend(self, audio_file) -> Optional[BytesIO]:
        files = {"file": ("record1.wav", audio_file, "multipart/form-data")}
        self.logger.debug(f"http://{self.config.backend_address}/raspi/")
        with stream(
            "POST",
            f"http://{self.config.backend_address}/raspi/",
            files=files,
            timeout=120,
        ) as response:
            self.logger.debug(response)
            if response.status_code == codes.OK:
                return BytesIO(response.read())
            else:
                return None

    async def load_buffer_file(self, path: PathLike):
        with open(path, "rb") as bf:
            return BytesIO(bf.read())

    async def ping_backend(self) -> bool:
        return (
            True
            if subprocess.run(
                ["ping", self.config.backend_address, "-c 1", "-i 0.4"],  # type: ignore[]
                capture_output=True,
            ).returncode
            == 0
            else False
        )


async def main() -> None:
    config = Config(CONFIG_FILE_NAME, __file__)
    system = System(config)
    logger = system.logger_manager.get_logger("Main")

    logger.debug("Play wellcome message")
    wellcome_audio_file = await system.load_buffer_file(WELLCOME_MESSAGE_PATH)
    await system.play_sound(wellcome_audio_file)

    # if not await system.ping_backend():
    #     connecting_audio_file = await system.load_buffer_file(CONNECTING_MESSAGE_PATH)
    #     await system.play_sound(connecting_audio_file)
    #     while not await system.ping_backend():
    #         sleep(PING_INTERVAL_SEC)
    #     connected_audio_file = await system.load_buffer_file(CONNECTED_MESSAGE_PATH)
    #     await system.play_sound(connected_audio_file)

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
    asyncio.run(main())
