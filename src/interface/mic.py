from pyaudio import PyAudio, paInt16
import time
from typing import Optional
import threading
import src.config.config as config
from src.log.log import log
import sounddevice as sd
import numpy as np
import io
import soundfile as sf


CHUNK = 1024 * 8
FORMAT = paInt16
CHANNELS = 2
RATE = 44100


class Mic:
    def __init__(self):
        self.logger = log.get_logger("Mic")
        self.device_name = config.get("mic_name")
        self.logger.info("Initialized.")

    def record(self) -> threading.Thread:
        thread = RecordThread(self.device_name)
        thread.start()
        return thread


mic = Mic()


class RecordThread(threading.Thread):
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
        self.logger.info("Initialized.")

    def run(self):
        sample_rate = 44100
        print("Recording... Press Enter to stop.")

        # 録音開始時の時間を取得
        audio = []

        def callback(indata, frames, time, status):
            audio.append(indata.copy())

        # ストリームを使って録音
        with sd.InputStream(samplerate=sample_rate, channels=2, callback=callback):
            while not self.stop_req:
                time.sleep(0.1)

        # 録音データを1つの配列にまとめる
        audio = np.concatenate(audio, axis=0)

            self.audio = audio
        self.sample_rate = sample_rate

        # self.logger.info("Run.")
        # py_audio = PyAudio()
        # buffer = BytesIO()
        # buffer.name = "record.wav"
        #
        # led.req(LedPattern.AudioListening)
        #
        # with wave.open(buffer, "wb") as wf:
        #     wf.setnchannels(CHANNELS)
        #     wf.setsampwidth(get_sample_size(FORMAT))
        #     wf.setframerate(RATE)
        #
        #     self.logger.info("Start recording.")
     
        # stream = py_audio.open(
        #         format=FORMAT,
        #         channels=CHANNELS,
        #         rate=RATE,
        #         input=True,
        #         input_device_index=self.get_device_index(py_audio),
        #     )
        #     while True:
        #         if self.stop_req:
        #             self.logger.info("Stop recording.")
        #             break
        #         else:
        #             wf.writeframes(stream.read(CHUNK, exception_on_overflow=False))
        #
        #     stream.close()
        #     py_audio.terminate()
        #
        # self.logger.info("Finalize record.")
        # buffer.seek(0)
        # self.buffer = buffer

    def get_device_index(self, py_audio: PyAudio = PyAudio()) -> Optional[int]:
        for index in range(py_audio.get_device_count()):
            if self.device_name in str(
                py_audio.get_device_info_by_index(index)["name"]
            ):
                self.logger.info(f"Found speaker. ({index=})")
                return index
        self.logger.error("Not found mic.")
        return None

    def stop(self):
        self.logger.info("Stop requested.")
        self.stop_req = True

    def get_recorded_file(self):
        audio_buffer = io.BytesIO()

        # 録音データを WAV 形式で BytesIO に保存
        sf.write(audio_buffer, self.audio, samplerate=self.sample_rate, format="WAV")

        # バッファのポインタを先頭に戻す
        audio_buffer.seek(0)

        return audio_buffer
