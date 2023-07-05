import logging
import inspect
import time
import toml


class LoggingHandler:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BRIGHT_RED = "\033[91m"
    RESET = "\033[0m"

    def __init__(self, log_level=logging.INFO, filename=None):
        self.logger = logging.getLogger(__name__)

        if not isinstance(log_level, int) or log_level < 0 or log_level > 50:
            print("Invalid log level specified. Defaulting to INFO.")
            log_level = logging.INFO

        self.logger.setLevel(log_level)

        if not self.logger.hasHandlers():
            try:
                config = toml.load("app_config.toml")
            except Exception as e:
                print(f"Error trying to load toml file: {e} ")
            try:
                logfilename = config["log_file"]
            except:
                logfilename = None
            if filename:
                handler = logging.FileHandler(filename)
            elif logfilename:
                handler = logging.FileHandler(logfilename)
            else:
                handler = logging.StreamHandler()
            self.logger.addHandler(handler)


    def _log(self, level, color, message, color_reset):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        f = inspect.currentframe()
        i = inspect.getframeinfo(f.f_back)
        self.logger.log(
            level,
            f"{timestamp} {color}{i.filename}:{i.lineno} {i.function} {message}{color_reset}",
        )

    def DEBUG(self, message):
        self._log(logging.DEBUG, self.GREEN, message, self.RESET)

    def INFO(self, message):
        self._log(logging.INFO, self.YELLOW, message, self.RESET)

    def WARNING(self, message):
        self._log(logging.WARNING, self.RED, message, self.RESET)

    def ERROR(self, message):
        self._log(logging.ERROR, self.BRIGHT_RED, message, self.RESET)

    def CRITICAL(self, message):
        self._log(logging.CRITICAL, self.BRIGHT_RED, message, self.RESET)


def main():
    logger = LoggingHandler(log_level=logging.DEBUG)
    logger.debug("A debug message to the logger.")
    logger.info("An info message.")


if __name__ == "__main__":
    main()
