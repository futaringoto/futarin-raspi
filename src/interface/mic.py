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
        wf.setnchannels(channels)
        wf.setsampwidth(get_sample_size(format))
        wf.setframerate(rate)

        logger.debug("Start recording")
        stream = py_audio.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=input_device_index,
        )
        while func():
            wf.writeframes(stream.read(chunk, exception_on_overflow=False))

        stream.close()
        py_audio.terminate()

    buffer.seek(0)
    logger.debug("Finish recording")
    return buffer


logger = getLogger("Mic")

chunk = 1024 * 8
format = paInt16
channels = 2
rate = 44100
input_device_index = 1

logger.debug("Initialized")

if __name__ == "__main__":
    logger.debug("Recording test")
    # TODO
