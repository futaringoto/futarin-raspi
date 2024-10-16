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


class RecordThread(threading.Thread):
    def __init__(
        self,
        device_name,
        logger=log.get_logger("MicRecordThread"),
        name="Mic-Record",
    ):
        super().__init__(name=name, daemon=True)
        self.device_name = device_name
        self.py_audio = PyAudio()
        self.logger = logger
        self.stop_req = False
        self.logger.info("Initialized.")
        self.buffer = BytesIO()
        self.buffer.name = "record.wav"
        self.mic_index = self.get_device_index(self.py_audio)

    def run(self):
        self.logger.info("Run.")

        led.req(LedPattern.AudioRecording)

        with wave.open(self.buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(get_sample_size(FORMAT))
            wf.setframerate(RATE)

            self.logger.info("Start recording.")
            stream = self.py_audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.mic_index,
            )
            while True:
                if self.stop_req:
                    self.logger.info("Stop recording.")
                    break
                else:
                    wf.writeframes(stream.read(CHUNK, exception_on_overflow=False))

            stream.close()
            self.py_audio.terminate()

        self.logger.info("Finalize record.")
        self.buffer.seek(0)
        self.buffer = self.buffer

    def get_device_index(self, py_audio: PyAudio = PyAudio()) -> Optional[int]:
        for index in range(py_audio.get_device_count()):
            if self.device_name in str(
                py_audio.get_device_info_by_index(index)["name"]
            ):
                self.logger.info(f"Found mic. ({index=})")
                return index
        self.logger.error("Not found mic.")
        return None

    def stop(self):
        self.logger.info("Stop requested.")
        self.stop_req = True

    def get_recorded_file(self):
        return self.buffer


class Mic:
    def __init__(self):
        self.logger = log.get_logger("Mic")
        self.device_name = config.get("mic_name")
        self.logger.info("Initialized.")

    def record(self, auto_start=True) -> RecordThread:
        thread = RecordThread(self.device_name)
        if auto_start:
            thread.start()
        return thread


mic = Mic()
