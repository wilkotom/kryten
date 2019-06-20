from typing import Optional
from abc import ABC, abstractmethod

class Session(ABC):
    @property
    @abstractmethod
    def session_id(self) -> str:
        pass

