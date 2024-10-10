from io import BytesIO
from os import PathLike
from sys import exit
from enum import Enum
from logging import getLogger
import asyncio
from typing import Optional
from httpx import stream, codes
from pydub import AudioSegment

import src.config.config as config
from src.interface.button import Button
from src.interface.mic import record
from src.interface.speaker import play_sound
from src.log.logger import get_logger

### CONST ###
WELCOME_MESSAGE_PATH: PathLike[str] = "assets/audio/welcome.wav"  # type: ignore
PLEASE_WAIT_MESSAGE_PATH: PathLike[str] = "assets/audio/please_wait.wav"  # type: ignore
FAIL_MESSAGE_PATH: PathLike[str] = "assets/audio/fail.wav"  # type: ignore
WHAT_HAPPEN_PATH: PathLike[str] = "assets/audio/whathappen.wav"  # type: ignore

SKIP_INTRODUCTION = config.get("skip_introduction");


### CLASS ###
class Processes(Enum):
    ListenMessage = 0
    TrainMessage = 1


## Interface ##
class Interface:
    def __init__(self) -> None:
        self.logger = getLogger("Interface")
        self.logger.debug(f"Left button Pin: {config.get('button_left_pin')}")
        self.button_left = Button(
            config.get("button_left_pin"), logger=get_logger("ButtonLeft")
        )
        self.logger.info("Initialized.")


class System:
    def __init__(self) -> None:
        self.interface = Interface()
        self.logger = get_logger("System")
        self.logger.info("Initialized.")

    async def train_message(self) -> None:
        self.logger.info("Train called.")
        whathappen = await self.load_buffer_file(WHAT_HAPPEN_PATH)
        await play_sound(whathappen)
        file = await record(self.interface.button_left.is_pressed)
        if not await self.check_recorded_file(file):
            fail_msg = await self.load_buffer_file(FAIL_MESSAGE_PATH)
            await play_sound(fail_msg)
            return
        backend_task = asyncio.create_task(self.call_backend(file))
        audio_file = await self.load_buffer_file(PLEASE_WAIT_MESSAGE_PATH)
        await play_sound(audio_file)
        processed_file = await backend_task
        if processed_file:
            await play_sound(processed_file)
        else:
            fail_msg = await self.load_buffer_file(FAIL_MESSAGE_PATH)
            await play_sound(fail_msg)

    async def check_recorded_file(self, audio_file) -> bool:
        audio = AudioSegment.from_file(audio_file, "wav")
        if audio.duration_seconds < 1:
            return False
        return True

    async def call_backend(self, audio_file) -> Optional[BytesIO]:
        url = f"{config.get('api_origin')}/v{config.get('api_version')}/raspi/"
        files = {"file": ("record.wav", audio_file, "multipart/form-data")}
        with stream(
            "POST",
            url,
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


async def main() -> None:
    system = System()
    logger = get_logger("Main")

    if not SKIP_INTRODUCTION:
        logger.info("Play welcome message.")
        welcome_audio_file = await system.load_buffer_file(WELCOME_MESSAGE_PATH)
        await play_sound(welcome_audio_file)

    logger.info("Start loop.")

    while True:
        try:
            await system.interface.button_left.wait_for_press()
            await system.train_message()
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    asyncio.run(main())
