from abc import ABC, abstractmethod
import threading

class BaseMonitor(threading.Thread, ABC):
    def __init__(self, name: str, logger):
        super().__init__(daemon=True, name=name)
        self.logger = logger

    @abstractmethod
    def run(self):
        pass 