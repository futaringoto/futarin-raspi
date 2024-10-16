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
            led.req(LedPattern.WifiHigh)

            self.logger.info("Wait for button to press or notifing.")
            done_task_index = await self.wait_multi_tasks(
                ct(api.wait_for_notification()),
                ct(button.wait_for_hold_main()),
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
                message_file = await api.get_message()

                if message_file:
                    self.logger.error("Success to get message_file.")
                    await button.wait_for_press_main()

                    playing_receive_message_thread = speaker.play_local_vox(
                        LocalVox.ReceiveMessage
                    )
                    playing_receive_message_thread.join()

                    led.req(LedPattern.AudioPlaying)
                    speaker.play(message_file).join()

                else:
                    self.logger.error("Failed to get message_file.")

            # if pressed button
            else:
                pressed_button = (
                    ButtonEnum.Main if done_task_index == 0 else ButtonEnum.Sub
                )

                self.logger.info(f"{pressed_button} was pressed.")

                if pressed_button == ButtonEnum.Main:
                    if self.mode == Mode.Normal:
                        self.logger.debug("Call normal mode.")
                        await self.normal()
                    else:
                        self.logger.debug("Call message mode.")
                        await self.message()
                else:
                    # observer sub button
                    done_task_index = await self.wait_multi_tasks(
                        ct(button.wait_for_release_sub()),
                        ct(button.wait_for_hold_sub()),
                    )
                    if done_task_index == 0:
                        await self.toggle_mode()
                    else:
                        self.logger.debug("Exit main_loop.")
                        return

    async def toggle_mode(self):
        self.logger.info("Toggle mode.")
        if self.mode == Mode.Normal:
            self.logger.info("Switch to message mode.")
            self.mode = Mode.Message
            messages_mode_message_thread = speaker.play_local_vox(LocalVox.MessagesMode)
            messages_mode_message_thread.join()

        else:
            self.mode = Mode.Normal
            self.logger.info("Switch to normal mode.")
            normal_mode_message_thread = speaker.play_local_vox(LocalVox.NormalMode)
            normal_mode_message_thread.join()

    async def message(self):
        self.logger.info("Start message mode")
        what_up_thread = speaker.play_local_vox(LocalVox.WhatUp)
        what_up_thread.join()

        self.logger.info("Record message to send.")
        recoard_thread = mic.record()
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()
        file = recoard_thread.get_recorded_file()
        if await api.messages(file):
            what_happen_thread = speaker.play_local_vox(LocalVox.SendMessage)
            what_happen_thread.join()
        else:
            what_happen_thread = speaker.play_local_vox(LocalVox.Fail)
            what_happen_thread.join()

    async def normal(self):
        self.logger.info("Start message mode")
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatUp)
        playing_what_happen_thread.join()

        self.logger.info("Record voice.")
        recoard_thread = mic.record()
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
        led.req(LedPattern.SystemTurnOff)
        await api.stop_listening_notifications()
        led.req(LedPattern.SystemOff)

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
