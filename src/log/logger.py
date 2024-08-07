from logging import getLogger, Formatter, StreamHandler, FileHandler, Logger, DEBUG

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


formatter = Formatter("%(asctime)s[%(levelname)s] %(name)s - %(message)s")

console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
console_handler.setFormatter(formatter)

file_handler = FileHandler(filename="futarin-raspi.log")
file_handler.setLevel(DEBUG)
file_handler.setFormatter(formatter)

logger = get_logger("LoggerManager")
logger.debug("initialized LoggerManager")


if __name__ == "__main__":
    logger = get_logger("Test")
    logger.debug("This is test message.")
