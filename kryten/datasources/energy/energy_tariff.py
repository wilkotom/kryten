from abc import ABC, abstractmethod


class EnergyTariff(ABC):
    @property
    @abstractmethod
    def current_energy_cost(self) -> float:
        pass
