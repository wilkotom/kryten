from kryten.datasources.energy.static_energy_tariff import StaticEnergyTariff


class TestStaticEnergyTariff:
    def test_current_energy_cost_returns_unit_rate(self):
        tariff = StaticEnergyTariff(unit_rate=0.25, standing_charge=0.30)
        assert tariff.current_energy_cost == 0.25

    def test_unit_rate_zero(self):
        tariff = StaticEnergyTariff(unit_rate=0.0, standing_charge=0.0)
        assert tariff.current_energy_cost == 0.0

    def test_standing_charge_does_not_affect_current_cost(self):
        tariff = StaticEnergyTariff(unit_rate=0.10, standing_charge=99.99)
        assert tariff.current_energy_cost == 0.10

    def test_default_unit_type_does_not_raise(self):
        tariff = StaticEnergyTariff(unit_rate=0.15, standing_charge=0.20)
        assert tariff.current_energy_cost == 0.15

    def test_explicit_unit_type(self):
        tariff = StaticEnergyTariff(unit_rate=0.10, standing_charge=0.20, unit_type="MWh")
        assert tariff.current_energy_cost == 0.10
