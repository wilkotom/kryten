from abc import ABC, abstractmethod

class SolarPowerInverter(ABC):
    """
    Provides a controller object allowing control of a network-connected
    Solar inverter
    """
    @property
    @abstractmethod
    def generation(self) -> float:
        pass
    @property
    @abstractmethod
    def battery_level(self) -> float:
        pass

    @property
    @abstractmethod
    def battery_discharge_rate(self) -> float:
        pass

    @property
    @abstractmethod
    def export_rate(self) -> float:
        pass