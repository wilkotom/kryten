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
    def illuminate(self, light_id: str) -> None:
        pass

    @abstractmethod
    def extinguish(self, light_id: str) -> None:
        pass


class SmartLightBulb(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def uuid(self):
        pass

    @property
    @abstractmethod
    def brightness(self) -> int:
        pass

    @property
    @abstractmethod
    def power(self) -> bool:
        pass

    @abstractmethod
    def sunrise(self) -> None:
        pass

    @abstractmethod
    def sunset(self) -> None:
        pass



