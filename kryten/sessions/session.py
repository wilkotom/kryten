import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Optional


class Session(ABC):
    @property
    @abstractmethod
    def session_id(self) -> Optional[str]:
        pass

    @abstractmethod
    def execute_api_call(self, path: str, payload: Dict[str, str], method: str) -> Union[HiveResponseObject,List[HiveResponseObject]]:
        pass
