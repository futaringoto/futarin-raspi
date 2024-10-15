import asyncio
from typing import Optional
from pydub import AudioSegment
from enum import Enum, auto

from src.log.log import log
from src.interface.mic import mic
from src.interface.wifi import wifi
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

    async def main(self):
        self.logger = log.get_logger("Main")
        await self.wait_for_network()
        await self.main_loop()
        await self.shutdown()
        self.logger.info("Initialized")

    async def main_loop(self):
        self.logger.info("Start main loop")
        self.logger.info("Play welcome message")
        playing_welcome_message_thread = speaker.play_local_vox(LocalVox.Welcome)

        self.logger.info("Establihs a WebSockets connection.")
        await api.req_ws_url()
        await api.start_listening_notification()

        while True:
            self.logger.info("Start infinity loop.")

            self.logger.info(
                "Wait for button to press or receiving notification on WebSockets."
            )
            wait_for_main_press_task = ct(button.wait_for_press_main())
            wait_for_sub_press_task = ct(button.wait_for_press_sub())
            wait_for_notification_task = ct(api.wait_for_notification())

            done_task_index = wait_multi_tasks(
                wait_for_main_press_task,
                wait_for_sub_press_task,
                wait_for_notification_task,
            )

            if done_task_index == 2:
                self.logger.debug("Checked notification")
                led.req(LedPattern.AudioReceive)

                received_file = await api.get_message()
                await button.wait_for_press_either()
                playing_welcome_message_thread.stop()
                playing_welcome_message_thread.join()

                playing_receive_message_thread = speaker.play_local_vox(
                    LocalVox.ReceiveMessage
                )
                playing_receive_message_thread.join()

                led.req(LedPattern.AudioResSuccess)
                log.logger.debug(received_file)
                speaker.play(received_file)

            else:
                self.logger.info("Try to stop welcome message.")
                playing_welcome_message_thread.stop()
                playing_welcome_message_thread.join()

                pressed_button = (
                    ButtonEnum.Main if done_task_index == 0 else ButtonEnum.Sub
                )

                self.logger.debug(f"{pressed_button} was pressed.")

                if pressed_button == ButtonEnum.Main:
                    if self.mode == Mode.Normal:
                        self.logger.debug("Call normal mode.")
                        await self.normal()
                    else:
                        self.logger.debug("Call message mode.")
                        await self.message()
                else:
                    self.logger.debug("Call switch_mode.")
                    await self.switch_mode()

    async def switch_mode(self):
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
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatHappen)
        playing_what_happen_thread.join()

        self.logger.info("Record message to send.")
        recoard_thread = mic.record()
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()
        file = recoard_thread.get_recorded_file()
        await api.messages(file)

        playing_what_happen_thread = speaker.play_local_vox(LocalVox.SendMessage)
        playing_what_happen_thread.join()

    async def normal(self):
        self.logger.info("Start message mode")
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatHappen)
        playing_what_happen_thread.join()

        recoard_thread = mic.record()
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()
        file = recoard_thread.get_recorded_file()
        if not await self.check_recorded_file(file):
            speaker.play_local_vox(LocalVox.KeepPressing)
            return
        while True:
            received_file = await api.normal(file)
            if received_file:
                thread = speaker.play(received_file)
                thread.join()
                break

    async def check_recorded_file(self, audio_file) -> bool:
        audio = AudioSegment.from_file(audio_file, "wav")
        if audio.duration_seconds < 1:
            return False
        return True

    async def shutdown(self):
        led.req(LedPattern.SystemTurnOff)

    async def wait_for_network(self):
        wait_for_wifi_enable_task = ct(wifi.wait_for_enable())
        wait_for_connect_to_api_task = ct(api.wait_for_connect())
        led.req(LedPattern.SystemSetup)

        done_task_index = await wait_multi_tasks(
            wait_for_wifi_enable_task,
            wait_for_connect_to_api_task,
        )

        if done_task_index == 0:
            await wait_for_connect_to_api_task

        led.req(LedPattern.WifiHigh)


async def wait_multi_tasks(
    *tasks: asyncio.Task, return_when=asyncio.FIRST_COMPLETED
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
