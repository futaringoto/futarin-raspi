import gpiozero
import asyncio
import src.config.config as config
from src.log.log import log
from enum import Enum, auto


MAIN_BUTTON_PIN = config.get("main_button_pin")
SUB_BUTTON_PIN = config.get("sub_button_pin")
SENSOR_INTERVAL = 0.1
MAIN_HOLD_TIME = 1
SUB_HOLD_TIME = 10


class ButtonEnum(Enum):
    Main = auto()
    Sub = auto()


class Button:
    def __init__(self) -> None:
        self.logger = log.get_logger("Button")
        self.main: gpiozero.Button = gpiozero.Button(
            MAIN_BUTTON_PIN, pull_up=True, hold_time=MAIN_HOLD_TIME
        )
        self.sub: gpiozero.Button = gpiozero.Button(
            SUB_BUTTON_PIN, pull_up=True, hold_time=SUB_HOLD_TIME
        )
        self.logger.info("Initialized.")

    async def wait_for_press_either(self) -> ButtonEnum:
        self.logger.debug("Create button pressed tasks")
        wait_for_main_press_task = asyncio.create_task(self.wait_for_press_main())
        wait_for_sub_press_task = asyncio.create_task(self.wait_for_press_sub())
        done, _ = await asyncio.wait(
            {wait_for_main_press_task, wait_for_sub_press_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for wait_for_main_press_task in done:
            if wait_for_main_press_task in done:
                return ButtonEnum.Main
        return ButtonEnum.Sub

    async def wait_for_press_main(self):
        self.logger.debug("Wait main button to press.")
        while not self.main.is_pressed:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def wait_for_release_main(self):
        self.logger.debug("Wait main button to release.")
        while self.main.is_pressed:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def wait_for_hold_main(self):
        self.logger.debug("Wait main button to hold.")
        while not self.main.is_held:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def wait_for_press_sub(self):
        self.logger.debug("Wait sub button to press.")
        while not self.sub.is_pressed:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def wait_for_release_sub(self):
        self.logger.debug("Wait sub button to release.")
        while self.sub.is_pressed:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def wait_for_hold_sub(self):
        self.logger.debug("Wait sub button to hold.")
        while not self.sub.is_held:
            await asyncio.sleep(SENSOR_INTERVAL)


button = Button()
