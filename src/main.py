import asyncio

import src.log.log as log
from src.interface.wifi import wifi
from src.backend.api import api
from src.interface.led import led, LedPattern
from src.interface.speaker import speaker, LocalVox
from src.interface.button import button

### Alias
ct = asyncio.create_task


async def main():
    logger = log.get_logger("Main")
    await wait_for_network()
    await main_loop()
    await shutdown()


async def main_loop():
    led.req(LedPattern.AudioResSuccess)
    playing_welcome_message_thread = speaker.play_local_vox(LocalVox.WelcomeVox)

    button.wait_for_push_both()


async def shutdown():
    led.req(LedPattern.SystemTurnOff)


async def wait_for_network():
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
    asyncio.run(main())
