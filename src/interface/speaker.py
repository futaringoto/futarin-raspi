from src.log.logger import get_logger
from pyaudio import PyAudio
import wave
from io import BytesIO
from typing import BinaryIO
from pydub import AudioSegment


async def play_sound(self, file: BinaryIO) -> None:
    logger.debug("Convert frame rate.")
    with wave.open(file, "rb") as wf:
        audio = AudioSegment.from_raw(
            file,
            sample_width=wf.getsampwidth(),
            frame_rate=wf.getframerate(),
            channels=wf.getnchannels(),
        )
        audio = audio.set_frame_rate(RATE)
        processed_file = BytesIO()
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

        self.logger.debug("Start playing sound.")
        while len(data := wf.readframes(1024 * 4)):
            stream.write(data)
        stream.close()
        p.terminate()
        self.logger.debug("Finish playing sound.")


logger = get_logger("Speaker")
RATE = 44100
logger.debug("Initialized.")
