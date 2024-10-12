from logging import getLogger, Formatter, StreamHandler, FileHandler, Logger, DEBUG
import json

LOG_FILE_NAME = "futarin-raspi.log"


class FileFormatter(Formatter):
    def format(self, record):
        return json.dumps(record.__dict__, default=str)


class Log:
    def __init__(self):
        self.loggers = []
        self.console_formatter = Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s]: %(message)s",
            datefmt="%H:%M:%S",
        )
        self.logger = self.get_logger("LoggerManager")
        self.logger.info("Initialized.")

        self.file_formatter = FileFormatter()
        self.file_handler = FileHandler(filename=LOG_FILE_NAME)
        self.file_handler.setLevel(DEBUG)
        self.file_handler.setFormatter(self.file_formatter)

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.console_formatter)

    def get_logger(self, name: str, console: bool = True, file: bool = True) -> Logger:
        logger = getLogger(name)
        logger.setLevel(DEBUG)
        if console:
            logger.addHandler(self.console_handler)
        if file:
            logger.addHandler(self.file_handler)
        self.loggers.append(self.logger)
        return logger


log = Log()
