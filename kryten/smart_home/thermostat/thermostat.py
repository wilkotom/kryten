from abc import ABC, abstractmethod
from typing import List, Dict, Union


class ThermostatZone(ABC):
    """Provides interfaces to interact with a single thermostat zone"""

    @property
    @abstractmethod
    def current_temperature(self) -> float:
        pass

    @property
    @abstractmethod
    def humidity(self) -> float:
        pass

    @property
    @abstractmethod
    def target_temperature(self) -> float:
        pass


class ThermostatController(ABC):
    """Provides a controller object for access to all the thermostats
    that belong to a particular home automation session"""

    @property
    @abstractmethod
    def zones(self) -> List[Dict[Union[int, str], str]]:
        pass


