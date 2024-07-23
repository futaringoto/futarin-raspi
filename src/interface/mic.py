from logging import getLogger, Logger
from typing import Optional
from pyaudio import PyAudio, get_sample_size, paInt16
from types import FunctionType
import wave
from io import BytesIO
from time import time


class Mic:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.chunk = 1024 * 3
        self.format = paInt16
        self.channels = 1
        self.rate = 44100
        self.resetPyAudio()
        self.logger.debug("Initialized Mic")

    def resetPyAudio(self) -> None:
        self.py_audio = PyAudio()

    async def record(self, func: FunctionType) -> BytesIO:
        self.resetPyAudio()
        self.logger.debug("Start recording")
        buffer = BytesIO()
        buffer.name = f"mic-voice-{int(time())}.wav"

        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(get_sample_size(self.format))
            wf.setframerate(self.rate)

            self.logger.debug("Start recording")
            stream = self.py_audio.open(
                format=self.format, channels=self.channels, rate=self.rate, input=True
            )
            while func():
                wf.writeframes(stream.read(self.chunk, exception_on_overflow=False))

            stream.close()
            self.py_audio.terminate()

        buffer.seek(0)
        self.logger.debug("Finish recording")
        return buffer
