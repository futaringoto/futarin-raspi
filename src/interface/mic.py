from logging import getLogger
from pyaudio import PyAudio, get_sample_size, paInt16
from typing import Callable
import wave
from io import BytesIO
from time import time


async def record(func: Callable[[], bool]) -> BytesIO:
    py_audio = PyAudio()
    buffer = BytesIO()
    buffer.name = f"mic-{int(time())}.wav"

    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(get_sample_size(FORMAT))
        wf.setframerate(RATE)

        logger.debug("Start recording")
        stream = py_audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
        )
        while func():
            wf.writeframes(stream.read(CHUNK, exception_on_overflow=False))

        stream.close()
        py_audio.terminate()

    buffer.seek(0)
    logger.debug("Finish recording")
    return buffer


logger = getLogger("Mic")

CHUNK = 1024 * 8
FORMAT = paInt16
CHANNELS = 2
RATE = 44100
INPUT_DEVICE_INDEX = 1

logger.debug("Initialized")

# if __name__ == "__main__":
#     logger.debug("Recording test")
#     # TODO
