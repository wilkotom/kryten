from abc import ABC, abstractmethod
from typing import List, Dict


class SmartLightController(ABC):
    """Provides a controller object for access to all the lights that belong to a particular home automation session"""

    @abstractmethod
    def list_lights(self) -> List[Dict[str, str]]:
        """Provides a list of the lights that the controller knows about, and their names"""
        pass


class SmartLightBulb(ABC):
    """Object which provides control over a single light bulb"""

    @property
    @abstractmethod
    def name(self):
        """Human-readable name for the bulb"""
        pass

    @property
    @abstractmethod
    def uuid(self):
        """Unique hardware identifier for the bulb"""
        pass

    @property
    @abstractmethod
    def brightness(self) -> int:
        """Sets / gets the current brightness of the bulb"""
        pass

    @property
    @abstractmethod
    def power(self) -> bool:
        """Sets / gets the current power status of the bulb"""
        pass

    @property
    @abstractmethod
    def _presence(self) -> bool:
        pass

    @abstractmethod
    def sunrise(self, period: int) -> None:
        """Gradually increases the bulb's brightness from 1% to 100% over the specified period """
        pass

    @abstractmethod
    def sunset(self, period: int) -> None:
        """Gradually decreases the bulb's brightness from 100% to 1% over the specified period """
        pass



