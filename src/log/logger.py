from logging import getLogger, Formatter, StreamHandler, FileHandler, Logger, DEBUG

class LoggerManager:
    def __init__(self) -> None:
        self.loggers = []

        self.formatter = Formatter('%(asctime)s[%(levelname)s] %(name)s - %(message)s')

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.formatter)

        self.file_handler = FileHandler(filename="futarin-raspi.log")
        self.file_handler.setLevel(DEBUG)
        self.file_handler.setFormatter(self.formatter)
        
        self.logger = self.get_logger("LoggerManager")
        self.logger.debug("initialized LoggerManager")

    def get_logger(self, name: str, console: bool = True, file: bool = True) -> Logger:
        logger = getLogger(name)
        logger.setLevel(DEBUG)
        if console:
            logger.addHandler(self.console_handler)
        if file:
            logger.addHandler(self.file_handler)
        self.loggers.append(logger)
        return logger

