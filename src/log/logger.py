from logging import getLogger, Formatter, StreamHandler, FileHandler, Logger, DEBUG
import json

LOG_FILE_NAME = "futarin-raspi.log"
loggers = []


def get_logger(name: str, console: bool = True, file: bool = True) -> Logger:
    logger = getLogger(name)
    logger.setLevel(DEBUG)
    if console:
        logger.addHandler(console_handler)
    if file:
        logger.addHandler(file_handler)
    loggers.append(logger)
    return logger


class FileFormatter(Formatter):
    def format(self, record):
        return json.dumps(record.__dict__)


console_formatter = Formatter(
    "%(asctime)s.%(msecs)d [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
)
file_formatter = FileFormatter()

console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
console_handler.setFormatter(console_formatter)

file_handler = FileHandler(filename=LOG_FILE_NAME)
file_handler.setLevel(DEBUG)
file_handler.setFormatter(file_formatter)

logger = get_logger("LoggerManager")
logger.debug("initialized LoggerManager")


if __name__ == "__main__":
    logger = get_logger("Test")
    logger.debug("This is test message.")
