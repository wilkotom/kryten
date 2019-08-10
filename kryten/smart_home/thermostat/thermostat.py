from abc import ABC, abstractmethod
from typing import List, Dict


class ThermostatController(ABC):
    """Provides a controller object for access to all the thermostats
    that belong to a particular home automation session"""

    @abstractmethod
    def list_zones(self) -> List[Dict[str, str]]:
        pass


class ThermostatZone(ABC):
    """Provides interfaces to interact with a single thermostat zone"""

    @property
    @abstractmethod
    def current_temperature(self) -> float:
        pass
