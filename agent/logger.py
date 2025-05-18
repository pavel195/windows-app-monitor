import logging
import os

class LoggerFactory:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def get_logger(self, name: str, filename: str, level=logging.INFO):
        logger = logging.getLogger(name)
        handler = logging.FileHandler(os.path.join(self.log_dir, filename), encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(level)
        return logger 