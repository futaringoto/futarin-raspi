import asyncio
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

    async def main_loop(self):
        # Play welcome message
        playing_welcome_message_thread = speaker.play_local_vox(LocalVox.Welcome)

        # Establish a WebSockets connection
        await api.req_ws_url()
        while True:
            wait_for_main_press_task = ct(button.wait_for_press_main())
            wait_for_sub_press_task = ct(button.wait_for_press_sub())
            # wait_for_notification_task = asyncio.create_task(
            #     api.wait_for_notification()
            # )

            done, _ = await asyncio.wait(
                {
                    wait_for_main_press_task,
                    wait_for_sub_press_task,
                    # wait_for_notification_task, # TODO
                },
                return_when=asyncio.FIRST_COMPLETED,
            )

            # if notified
            if False and wait_for_notification_task in done:
                self.logger.debug("Notified")
                message_id = await wait_for_notification_task
                self.logger.debug(f"message_id = {message_id}")
                led.req(LedPattern.AudioReceive)

                received_file = await api.get_message(message_id)
                await button.wait_for_press_either()

                playing_receive_message_thread = speaker.play_local_vox(
                    LocalVox.ReceiveMessage
                )
                playing_receive_message_thread.join()
                speaker.play(received_file)
            else:
                playing_welcome_message_thread.stop()
                playing_welcome_message_thread.join()

                pressed_button = (
                    ButtonEnum.Main
                    if wait_for_main_press_task in done
                    else ButtonEnum.Sub
                )

                self.logger.debug(pressed_button)

                if pressed_button == ButtonEnum.Main:
                    if self.mode == Mode.Normal:
                        await self.normal()
                    else:
                        await self.message()
                else:
                    await self.switch_mode()

    async def switch_mode(self):
        if self.mode == Mode.Normal:
            self.mode = Mode.Message
            messages_mode_message_thread = speaker.play_local_vox(LocalVox.MessagesMode)
            messages_mode_message_thread.join()

        else:
            self.mode = Mode.Normal
            normal_mode_message_thread = speaker.play_local_vox(LocalVox.NormalMode)
            normal_mode_message_thread.join()

    async def message(self):
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatHappen)
        playing_what_happen_thread.join()

        recoard_thread = mic.record()
        await button.wait_for_release_main()
        recoard_thread.stop()
        recoard_thread.join()
        file = recoard_thread.get_recorded_file()
        await api.messages(file)

        playing_what_happen_thread = speaker.play_local_vox(LocalVox.SendMessage)
        playing_what_happen_thread.join()

    async def normal(self):
        playing_what_happen_thread = speaker.play_local_vox(LocalVox.WhatHappen)
        playing_what_happen_thread.join()

        print(0)
        recoard_thread = mic.record()
        print(1)
        await button.wait_for_release_main()
        print(2)
        recoard_thread.stop()
        print(3)
        recoard_thread.join()
        print(4)
        file = recoard_thread.get_recorded_file()
        print(5)
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

        done, pending = await asyncio.wait(
            (wait_for_wifi_enable_task, wait_for_connect_to_api_task),
            return_when=asyncio.FIRST_COMPLETED,
        )

        if wait_for_wifi_enable_task in done:
            # led.req(wifi.strength()) # TODO
            await wait_for_connect_to_api_task

        # if wait_for_connect_to_api_task is done
        led.req(LedPattern.WifiHigh)


if __name__ == "__main__":
    main = Main()
    asyncio.run(main.main())
