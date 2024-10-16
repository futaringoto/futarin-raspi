from pyaudio import PyAudio
import threading
import wave
from io import BytesIO
from typing import BinaryIO, Optional
from pydub import AudioSegment
import src.config.config as config
from src.log.log import log
from enum import Enum, auto
from os import PathLike
from typing import Dict


DELTA_VOLUME = config.get("delta_volume")
RATE = 44100
CHUNK = 1024 * 4


class LocalVox(Enum):
    Welcome = auto()
    Shutdown = auto()
    WhatUp = auto()
    KeepPressing = auto()
    MessagesMode = auto()
    NormalMode = auto()
    SendMessage = auto()
    ReceiveMessage = auto()
    Fail = auto()


local_vox_paths: Dict[LocalVox, str | PathLike] = {
    LocalVox.Welcome: "assets/vox/welcome.wav",
    LocalVox.Shutdown: "assets/vox/shutdown.wav",  # TODO
    LocalVox.WhatUp: "assets/vox/whatup.wav",
    LocalVox.KeepPressing: "assets/vox/fail.wav",  # TODO
    LocalVox.Fail: "assets/vox/fail.wav",
    LocalVox.MessagesMode: "assets/vox/message_mode.wav",
    LocalVox.NormalMode: "assets/vox/normal.wav",
    LocalVox.SendMessage: "assets/vox/send_message.wav",
    LocalVox.ReceiveMessage: "assets/vox/receive_message.wav",
}


class PlayThread(threading.Thread):
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
        self.logger.info("Initialized")

    def run(self):
        self.logger.info("Run")
        self.logger.info("Convert framerate and volume.")
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
                    self.logger.info("Stop playing sound.")
                    break
            stream.close()
            p.terminate()
            self.logger.info("Finish playing sound.")

    def get_device_index(self, py_audio: PyAudio = PyAudio()) -> Optional[int]:
        for index in range(py_audio.get_device_count()):
            if self.device_name in str(
                py_audio.get_device_info_by_index(index)["name"]
            ):
                self.logger.info(f"Found speaker. ({index=})")
                return index
        self.logger.error("Not found speaker.")
        return None

    def stop(self):
        self.logger.info("Stop requested.")
        self.stop_req = True


class Speaker:
    def __init__(self):
        self.logger = log.get_logger("Speaker")
        self.device_name = config.get("speaker_name")
        self.logger.info("Initialized")

    def play_local_vox(self, local_vox: LocalVox) -> PlayThread:
        self.logger.info(f"play local vox. ({local_vox=})")
        path = local_vox_paths[local_vox]
        return self.play_by_path(path)

    def play_by_path(self, path: str | PathLike) -> PlayThread:
        self.logger.info(f"Play sound by path. ({path=})")
        with open(path, "rb") as bf:
            buffer_file = BytesIO(bf.read())
            return self.play(buffer_file)

    def play(self, file: BinaryIO) -> PlayThread:
        self.logger.info("Play sound.")
        thread = PlayThread(file, self.device_name)
        thread.start()
        return thread


speaker = Speaker()
