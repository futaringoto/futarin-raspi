import gpiozero
import asyncio
import src.config.config as config
from src.log.log import log
from enum import Enum, auto


MAIN_BUTTON_PIN = config.get("main_button_pin")
SUB_BUTTON_PIN = config.get("sub_button_pin")


class ButtonEnum(Enum):
    Main = auto()
    Sub = auto()


class Button:
    def __init__(self) -> None:
        self.logger = log.get_logger("Button")
        self.main: gpiozero.Button = gpiozero.Button(MAIN_BUTTON_PIN, pull_up=True)
        self.sub: gpiozero.Button = gpiozero.Button(SUB_BUTTON_PIN, pull_up=True)
        self.logger.info("Initialized.")

    async def wait_for_press_either(self) -> ButtonEnum:
        wait_for_main_press_task = asyncio.create_task(self.wait_for_press_main())
        wait_for_sub_press_task = asyncio.create_task(self.wait_for_press_sub())
        done, _ = await asyncio.wait(
            {wait_for_main_press_task, wait_for_sub_press_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in done:
            if wait_for_main_press_task in done:
                return ButtonEnum.Main
        return ButtonEnum.Sub

    async def wait_for_release_main(self):
        while self.main.is_pressed:
            await asyncio.sleep(0.1)

    async def wait_for_press_main(self):
        while not self.main.is_pressed:
            await asyncio.sleep(0.1)

    async def wait_for_press_sub(self):
        while not self.sub.is_pressed:
            await asyncio.sleep(0.1)


button = Button()
