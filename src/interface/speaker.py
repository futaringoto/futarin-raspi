from src.log.logger import get_logger
from pyaudio import PyAudio
import wave
from io import BytesIO
from typing import BinaryIO, Optional
from pydub import AudioSegment

import src.config.config as config

DELTA_VOLUME = config.get("delta_volume");
RATE = 44100
CHUNK = 1024 * 4


async def play_sound(file: BinaryIO) -> None:
    logger.info("Convert framerate.")
    with wave.open(file, "rb") as wf:
        audio = AudioSegment.from_raw(
            file,
            sample_width=wf.getsampwidth(),
            frame_rate=wf.getframerate(),
            channels=wf.getnchannels(),
        )
        audio = audio.set_frame_rate(RATE) + DELTA_VOLUME
        processed_file = BytesIO()
        processed_file = audio.export(processed_file, format="wav")

    with wave.open(processed_file, "rb") as wf:
        p = PyAudio()
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=DEVICE_INDEX,
        )

        logger.info("Start playing sound.")
        while len(data := wf.readframes(CHUNK)):
            stream.write(data)
        stream.close()
        p.terminate()
        logger.info("Finish playing sound.")


def get_device_index(py_audio: PyAudio, device_name: str) -> Optional[int]:
    for index in range(py_audio.get_device_count()):
        if device_name in str(py_audio.get_device_info_by_index(index)["name"]):
            return index
    return None


logger = get_logger("Speaker")

DEVICE_INDEX = get_device_index(PyAudio(), config.get("output_audio_device_name"))

logger.info("Initialized.")
