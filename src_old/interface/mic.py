from pyaudio import PyAudio, get_sample_size, paInt16
from typing import Callable, Optional
import wave
from io import BytesIO
from time import time

import src.config.config as config
from src.log.logger import get_logger

CHUNK = 1024 * 8
FORMAT = paInt16
CHANNELS = 2
RATE = 44100


async def record(func: Callable[[], bool]) -> BytesIO:
    py_audio = PyAudio()
    buffer = BytesIO()
    buffer.name = f"mic-{int(time())}.wav"

    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(get_sample_size(FORMAT))
        wf.setframerate(RATE)

        logger.info("Start recording.")
        stream = py_audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
        )
        while func():
            wf.writeframes(stream.read(CHUNK, exception_on_overflow=False))

        stream.close()
        py_audio.terminate()

    buffer.seek(0)
    logger.info("Finish recording.")
    return buffer


def get_device_index(py_audio: PyAudio, device_name: str) -> Optional[int]:
    for index in range(py_audio.get_device_count()):
        if device_name in str(py_audio.get_device_info_by_index(index)["name"]):
            return index
    return None


logger = get_logger("Mic")

DEVICE_INDEX = get_device_index(PyAudio(), config.get("input_audio_device_name"))

logger.debug("Initialized")
