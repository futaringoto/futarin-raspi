from pyaudio import PyAudio
import threading
import wave
from io import BytesIO
from typing import BinaryIO, Optional
from pydub import AudioSegment
import src.config.config as config
import src.log.log as log
from enum import Enum, auto
from os import PathLike
from typing import Dict


DELTA_VOLUME = config.get("delta_volume")
RATE = 44100
CHUNK = 1024 * 4


class LocalVox(Enum):
    WelcomeVox = auto()
    ShutdownVox = auto()


local_vox_paths: Dict[LocalVox, str | PathLike] = {
    LocalVox.WelcomeVox: "assets/vox/welcome.mp3",
    LocalVox.ShutdownVox: "assets/vox/shutdown.mp3",  # TODO
}


class Speaker:
    def __init__(self):
        self.logger = log.get_logger("Speaker")
        self.device_name = config.get("output_audio_device_name")

    def play_local_vox(self, local_vox: LocalVox) -> threading.Thread:
        path = local_vox_paths[local_vox]
        return self.play_by_path(path)

    def play_by_path(self, path: str | PathLike) -> threading.Thread:
        with open(path, "rb") as bf:
            buffer_file = BytesIO(bf.read())
            return self.play(buffer_file)

    def play(self, file: BinaryIO) -> threading.Thread:
        thread = self.play_for_thread(file, self.device_name)
        thread.run()
        return thread

    class play_for_thread(threading.Thread):
        def __init__(
            self,
            file: BinaryIO,
            device_name,
            logger=log.get_logger("SpeakerPlayThread"),
            name="Speaker-Play",
        ):
            super().__init__(name=name)
            self.file = file
            self.device_name = device_name
            self.logger = logger
            self.stop_req = False

        def run(self):
            self.logger.info("Convert framerate.")
            with wave.open(self.file, "rb") as wf:
                audio = AudioSegment.from_raw(
                    self.file,
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
                    output_device_index=self.get_device_index(p),
                )

                self.logger.info("Start playing sound.")
                while len(data := wf.readframes(CHUNK)):
                    if not self.stop_req:
                        stream.write(data)
                    else:
                        self.logger.info("Stopped.")
                        break
                stream.close()
                p.terminate()
                self.logger.info("Finish playing sound.")

        def get_device_index(self, py_audio: PyAudio = PyAudio()) -> Optional[int]:
            for index in range(py_audio.get_device_count()):
                if self.device_name in str(
                    py_audio.get_device_info_by_index(index)["name"]
                ):
                    return index
            return None

        def stop(self):
            self.stop_req = True


speaker = Speaker()
