import gpiozero
import src.config.config as config
import src.log.log as log


MAIN_BUTTON_PIN, SUB_BUTTON_PIN = config.get("main_button_pin", "sub_button_pin")


class Button:
    def __init__(self) -> None:
        self.logger = log.get_logger("Button")
        self.main: gpiozero.Button = gpiozero.Button(MAIN_BUTTON_PIN)
        self.sub: gpiozero.Button = gpiozero.Button(SUB_BUTTON_PIN)
        self.logger.info("Initialized.")

    async def wait_for_push_both(self):
        await self.main.wait_for_press()

    async def wait_for_push_main(self):
        await self.main.wait_for_press()

    async def wait_for_push_sub(self):
        await self.sub.wait_for_press()

    async def wait_for_press(self) -> None:
        self.logger.info("Start waiting for pressed.")
        self.button.wait_for_press()  # type: ignore
        self.logger.info("Pressed during waiting.")
        return

    async def wait_for_release(self) -> None:
        self.logger.info("Start waiting for released.")
        self.button.wait_for_release()  # type: ignore
        self.logger.info("Released during waiting.")
        return


button = Button()
