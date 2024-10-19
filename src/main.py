import asyncio
from typing import Optional
from pydub import AudioSegment
from pydub.exceptions import PydubException
from enum import Enum, auto


from src.log.log import log
from src.interface.mic import mic
from src.backend.api import api
from src.interface.led import led, LedPattern
from src.interface.speaker import speaker, LocalVox
from src.interface.button import button, ButtonEnum

### Alias
ct = asyncio.create_task


class Mode(Enum):
    Normal = auto()
    Message = auto()


class Main:
    def __init__(self):
        self.mode = Mode.Normal
        self.last_converted_file = None
        self.logger = log.get_logger("Main")
        self.logger.info("Initialized")

    async def main(self):
        self.logger.info("Start Main.main")
        await self.setup()
        await self.main_loop()
        await self.shutdown()

    async def setup(self):
        led.req(LedPattern.SystemSetup)
        await api.wait_for_connect()
        await api.start_listening_notifications()

    async def main_loop(self):
        self.logger.info("Start Main.main_loop")
        welcome_message_thread = speaker.play_local_vox(LocalVox.Welcome)

        while True:
            self.logger.info("Start loop.")
            # reset led
            led.req(LedPattern.WifiHigh)

            self.logger.info("Wait for button to press or notifing.")
            done_task_index = await self.wait_multi_tasks(
                ct(api.wait_for_notification()),
                ct(button.wait_for_press_main()),
                ct(button.wait_for_press_sub()),
            )

            # Try to stop welcome message
            if welcome_message_thread.is_alive():
                self.logger.info("Stop welcome message.")
                welcome_message_thread.stop()
                welcome_message_thread.join()

            # if notified
            if done_task_index == 0:
                self.logger.debug("Notified.")
                response_file = await api.get_message()

                if response_file is None:
                    self.logger.error("Failed to get message_file")
                else:
                    self.logger.error("Success to get message_file.")
                    led.req(LedPattern.Notifing)
                    await button.wait_for_press_main()

                    speaker.play_local_vox(LocalVox.ReceiveMessage).join()

                    led.req(LedPattern.AudioPlaying)
                    speaker.play(response_file).join()

            # if button pressed
            else:
                pressed_button = (
                    ButtonEnum.Main if done_task_index == 1 else ButtonEnum.Sub
                )
                self.logger.info(f"{pressed_button} was pressed.")

                # if main button pressed
                if pressed_button == ButtonEnum.Main:
                    if self.mode == Mode.Normal:
                        self.logger.debug("Call normal mode.")
                        await self.normal()
                    else:
                        self.logger.debug("Call message mode.")
                        await self.message()

                # if sub button pressed
                else:
                    # observe sub button
                    done_task_index = await self.wait_multi_tasks(
                        ct(button.wait_for_release_sub()),
                        ct(button.wait_for_hold_sub()),
                    )
                    if done_task_index == 0:
                        self.logger.info("Released sub button during waiting holding.")
                        await self.toggle_mode()
                    else:
                        self.logger.info("Holded sub button.")
                        self.logger.debug("Exit main_loop.")
                        return

    async def toggle_mode(self):
        self.logger.info("Toggle mode.")
        if self.mode == Mode.Normal:
            self.logger.info("Switch to message mode.")
            self.mode = Mode.Message
            speaker.play_local_vox(LocalVox.MessagesMode).join()

        else:
            self.mode = Mode.Normal
            self.logger.info("Switch to normal mode.")
            speaker.play_local_vox(LocalVox.NormalMode).join()

    async def message(self):
        self.logger.info("Start message mode")
        speaker.play_local_vox(LocalVox.WhatUp).join()

        self.logger.info("Record voice.")
        recoard_thread = mic.record()
        led.req(LedPattern.AudioRecording)
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()

        self.logger.info("Check recorded file.")
        recorded_file = recoard_thread.get_recorded_file()
        audio_seconds = self.get_audio_seconds(recorded_file)
        if audio_seconds is None:
            self.logger.info("Inviled recorded file.")
            speaker_thread = speaker.play_local_vox(LocalVox.Fail)
            speaker_thread.join()
            return
        elif audio_seconds < 1:
            self.logger.info("Recorded file is short.")
            if self.last_converted_file is not None:
                self.logger.info("Post converted file.")
                is_succses = await api.post_message(self.last_converted_file)
                if is_succses:
                    led.req(LedPattern.ApiSuccess)
                    speaker.play_local_vox(LocalVox.SendMessage).join()
                else:
                    await self.fail()

        else:
            self.logger.info("Convert recorded message.")
            response_file = api.conversion(recorded_file)
            if response_file is None:
                await self.fail()
            else:
                led.req(LedPattern.ApiSuccess)
                self.last_converted_file = response_file
                speaker.play(response_file).join()

    async def fail(self):
        led.req(LedPattern.ApiFail)
        speaker_thread = speaker.play_local_vox(LocalVox.Fail)
        speaker_thread.join()

    async def normal(self):
        self.logger.info("Start message mode")
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatUp)
        playing_what_happen_thread.join()

        self.logger.info("Record voice.")
        recoard_thread = mic.record()
        led.req(LedPattern.AudioRecording)
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()

        self.logger.info("Check recorded file.")
        file = recoard_thread.get_recorded_file()
        audio_seconds = self.get_audio_seconds(file)
        if audio_seconds is None or audio_seconds < 1:
            self.logger.info("Inviled recorded file.")
            speaker_thread = speaker.play_local_vox(LocalVox.Fail)
            speaker_thread.join()
            return

        self.logger.info("Call api.normal")
        received_file = await api.normal(file)
        if received_file is None:
            speaker_thread = speaker.play_local_vox(LocalVox.Fail)
            speaker_thread.join()
        else:
            speaker_thread = speaker.play(received_file)
            led.req(LedPattern.AudioPlaying)
            speaker_thread.join()

    def get_audio_seconds(self, audio_file) -> Optional[int]:
        try:
            audio = AudioSegment.from_file(audio_file, "wav")
            return audio.duration_seconds
        except PydubException:
            self.logger.error("Failed to convert recorded audio to AudioSegment.")
            return None

    async def shutdown(self):
        self.logger.info("Shutdown.")
        led.req(LedPattern.SystemOff)
        await api.stop_listening_notifications()
        led.req(LedPattern.SystemTurnOff)

    async def wait_multi_tasks(
        self, *tasks: asyncio.Task, return_when=asyncio.FIRST_COMPLETED
    ) -> Optional[int]:
        done, pending = await asyncio.wait(
            tasks,
            return_when=return_when,
        )

        done_task_index = None

        for idx, task in enumerate(tasks):
            if task in done:
                done_task_index = idx

        for pending_task in pending:
            pending_task.cancel()

        return done_task_index


if __name__ == "__main__":
    main = Main()
    asyncio.run(main.main())
