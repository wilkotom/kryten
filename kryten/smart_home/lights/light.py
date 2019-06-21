from abc import ABC, abstractmethod
from typing import List, Dict;


class SmartLightController(ABC):

    @abstractmethod
    def list_lights(self) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def brightness(self, light_id: str) -> None:
        pass

    @abstractmethod
    def illuminate(self, light_id: str) -> bool:
        pass

    @abstractmethod
    def extinguish(self, light_id: str) -> bool:
        pass


class SmartLightBulb(ABC):

    @property
    @abstractmethod
    def brightness(self) -> int:
        pass

    @property
    @abstractmethod
    def power(self) -> bool:
        pass




