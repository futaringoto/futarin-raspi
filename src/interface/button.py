from logging import getLogger, Logger
from typing import Optional
import gpiozero

class Button:
    def __init__(self, pin: int, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.gpiozero_button: gpiozero.Button = gpiozero.Button(pin)
        self.logger.debug(f"Initialized Button(pin:{pin})")
    def is_pressed(self) -> bool:
        return self.gpiozero_button.value == 1
    def is_hold(self) -> bool:
        return self.gpiozero_button.value == 0
    async def wait_for_press(self) -> None:
        self.logger.debug("Start waiting for button pressed")
        self.gpiozero_button.wait_for_press() # type: ignore
        self.logger.debug("Button pressed during waiting")
        return
    async def wait_for_release(self) -> None:
        self.logger.debug("Start waiting for button released")
        self.gpiozero_button.wait_for_release() # type: ignore
        self.logger.debug("Button released during waiting")
        return

