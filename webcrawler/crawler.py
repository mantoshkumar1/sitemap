import logging

class Crawler:
    def __init__(self):
        self.logger = logging.getLogger ( __name__ )
        self.set_log_level(10)

    def set_log_level( self, user_log_level=2 ):
        # todo: take user_log_level as optional args from command prompt
        # Reference: https://docs.python.org/2/howto/logging.html#logging-levels
        std_logging_levels = {
            0: logging.NOTSET,  # lowest priority
            1: logging.DEBUG,
            2: logging.INFO,
            3: logging.WARNING,
            4: logging.ERROR,
            5: logging.CRITICAL,  # highest priority
        }

        mapped_log_level = std_logging_levels.get ( user_log_level )
        if not mapped_log_level:
            mapped_log_level = std_logging_levels[2]

        logging.getLogger ().setLevel ( mapped_log_level )

        self.logger.info("test debug")