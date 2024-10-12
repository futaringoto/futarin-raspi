from pyaudio import PyAudio, get_sample_size, paInt16
from src.interface.led import led, LedPattern
from typing import Optional
import wave
from io import BytesIO
import threading
import src.config.config as config
from src.log.log import log


CHUNK = 1024 * 8
FORMAT = paInt16
CHANNELS = 2
RATE = 44100


class Mic:
    def __init__(self):
        self.logger = log.get_logger("Mic")
        self.device_name = config.get("input_audio_device_name")

    def record(self) -> threading.Thread:
        thread = self.record_for_thread(self.device_name)
        thread.start()
        return thread

    class record_for_thread(threading.Thread):
        def __init__(
            self,
            device_name,
            logger=log.get_logger("MicRecordThread"),
            name="Mic-Record",
        ):
            super().__init__(name=name)
            self.device_name = device_name
            self.logger = logger
            self.stop_req = False

        def run(self):
            py_audio = PyAudio()
            buffer = BytesIO()
            buffer.name = "record.wav"

            led.req(LedPattern.AudioListening)

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
                    input_device_index=self.get_device_index(py_audio),
                )
                while not self.stop_req:
                    wf.writeframes(stream.read(CHUNK, exception_on_overflow=False))

                stream.close()
                py_audio.terminate()

            buffer.seek(0)
            logger.info("Finish recording.")
            self.buffer = buffer

        def get_device_index(self, py_audio: PyAudio = PyAudio()) -> Optional[int]:
            for index in range(py_audio.get_device_count()):
                if self.device_name in str(
                    py_audio.get_device_info_by_index(index)["name"]
                ):
                    return index
            return None

        def stop(self):
            self.stop_req = True

        def get_recorded_file(self):
            return self.buffer


mic = Mic()


def get_device_index(py_audio: PyAudio, device_name: str) -> Optional[int]:
    for index in range(py_audio.get_device_count()):
        if device_name in str(py_audio.get_device_info_by_index(index)["name"]):
            return index
    return None


logger = log.get_logger("Mic")


logger.debug("Initialized")
