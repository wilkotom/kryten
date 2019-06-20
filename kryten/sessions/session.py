import requests
from abc import ABC, abstractmethod
from typing import Dict

class Session(ABC):
    @property
    @abstractmethod
    def session_id(self) -> str:
        pass

    @abstractmethod
    def execute_api_call(self, path: str, payload: Dict[str, str], method: str) -> requests.Response:
        pass
