from kryten.datasources.energy.energy_tariff import EnergyTariff


class StaticEnergyTariff(EnergyTariff):
    def __init__(self, unit_rate: float, standing_charge: float, unit_type: str = "kWh"):
        self.__unit_rate = unit_rate
        self.__standing_charge = standing_charge
        self.__unit_type = unit_type

    @property
    def current_energy_cost(self) -> float:
        return self.__unit_rate
