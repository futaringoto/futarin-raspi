from os import path
from logging import getLogger, Logger
import subprocess
from typing import Optional

class RingLED:
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        dir_name = path.dirname(__file__)
        ring_led_script_path = path.join(dir_name, "ring_led_pipe.py")
        self.ring_led_popen: subprocess.Popen = subprocess.Popen(
            ["sudo", "python3", ring_led_script_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.logger.debug("Initialized Ring LED")
    def flash(self) -> None:
        self.ring_led_popen.stdin.write(b'xyz')

