import pytest
from unittest.mock import MagicMock, patch
from time import time

from kryten.smart_home.thermostat.tado import TadoThermostatZone, TadoThermostatController
from kryten.exceptions import UnexpectedResultError


ZONE_STATE = {
    "sensorDataPoints": {
        "humidity": {"percentage": 55.0},
        "insideTemperature": {"celsius": 21.5},
    },
    "setting": {
        "power": "ON",
        "temperature": {"celsius": 22.0},
    },
}

ZONE_LIST = [
    {"id": 1, "name": "Living Room", "type": "HEATING"},
    {"id": 2, "name": "Bedroom", "type": "HEATING"},
    {"id": 3, "name": "Hot Water", "type": "HOT_WATER"},
]

WEATHER_RESPONSE = {
    "solarIntensity": {"percentage": 42.0},
    "outsideTemperature": {"celsius": 8.5},
}


def make_mock_session(home_id="12345"):
    session = MagicMock()
    session.home_id = home_id
    return session


class TestTadoThermostatZone:
    def test_initial_state_is_fetched_on_construction(self):
        session = make_mock_session()
        session.execute_api_call.return_value = ZONE_STATE
        zone = TadoThermostatZone(session, zone_id=1)
        assert zone.current_temperature == 21.5
        assert zone.humidity == 55.0
        assert zone.target_temperature == 22.0

    def test_state_is_cached_within_min_refresh(self):
        session = make_mock_session()
        session.execute_api_call.return_value = ZONE_STATE
        zone = TadoThermostatZone(session, zone_id=1, min_refresh=300)
        session.execute_api_call.reset_mock()
        # Access all properties — none should trigger a new API call
        _ = zone.current_temperature
        _ = zone.humidity
        _ = zone.target_temperature
        session.execute_api_call.assert_not_called()

    def test_state_is_refreshed_after_min_refresh(self):
        session = make_mock_session()
        session.execute_api_call.return_value = ZONE_STATE
        zone = TadoThermostatZone(session, zone_id=1, min_refresh=0)
        session.execute_api_call.reset_mock()
        _ = zone.current_temperature
        # min_refresh=0 means every access should trigger a refresh
        assert session.execute_api_call.call_count >= 1

    def test_list_response_raises_unexpected_result_error(self):
        session = make_mock_session()
        session.execute_api_call.return_value = [1, 2, 3]
        with pytest.raises(UnexpectedResultError):
            TadoThermostatZone(session, zone_id=1)

    def test_null_target_temperature_falls_back_to_current_temperature(self):
        session = make_mock_session()
        state_with_null = {
            "sensorDataPoints": {
                "humidity": {"percentage": 55.0},
                "insideTemperature": {"celsius": 21.5},
            },
            "setting": {
                "power": "ON",
                "temperature": None,
            },
        }
        session.execute_api_call.return_value = state_with_null
        zone = TadoThermostatZone(session, zone_id=1)
        assert zone.target_temperature == 21.5

    def test_power_off_state_is_parsed(self):
        session = make_mock_session()
        state_off = {
            "sensorDataPoints": {
                "humidity": {"percentage": 55.0},
                "insideTemperature": {"celsius": 19.0},
            },
            "setting": {
                "power": "OFF",
                "temperature": {"celsius": 18.0},
            },
        }
        session.execute_api_call.return_value = state_off
        zone = TadoThermostatZone(session, zone_id=1)
        assert zone._power is False


class TestTadoThermostatController:
    def _make_controller(self, zone_list=None, zone_state=None, weather=None):
        if zone_list is None:
            zone_list = ZONE_LIST
        if zone_state is None:
            zone_state = ZONE_STATE
        if weather is None:
            weather = WEATHER_RESPONSE

        session = make_mock_session()

        def side_effect(path, *args, **kwargs):
            if "weather" in path:
                return weather
            if "state" in path:
                return zone_state
            return zone_list

        session.execute_api_call.side_effect = side_effect
        return TadoThermostatController(session), session

    def test_zones_contains_only_heating_zones(self):
        controller, _ = self._make_controller()
        zone_names = [z["name"] for z in controller.zones]
        assert "Living Room" in zone_names
        assert "Bedroom" in zone_names
        assert "Hot Water" not in zone_names

    def test_singleton_zone_list_response_raises_unexpected_result(self):
        session = make_mock_session()
        session.execute_api_call.return_value = {"not": "a list"}
        with pytest.raises(UnexpectedResultError):
            TadoThermostatController(session)

    def test_zone_list_is_cached_on_repeated_access(self):
        controller, session = self._make_controller()
        call_count = session.execute_api_call.call_count
        _ = controller.zones
        assert session.execute_api_call.call_count == call_count

    def test_weather_is_fetched_when_timestamp_is_stale(self):
        controller, session = self._make_controller()
        controller._weather_timestamp = 0.0
        session.execute_api_call.reset_mock()
        _ = controller.external_temperature
        weather_calls = [
            c for c in session.execute_api_call.call_args_list
            if "weather" in str(c)
        ]
        assert len(weather_calls) >= 1

    def test_weather_is_not_fetched_when_timestamp_is_fresh(self):
        controller, session = self._make_controller()
        controller._weather_timestamp = time() + 10_000
        controller._outside_temperature = 10.0
        controller._solar_intensity = 50.0
        session.execute_api_call.reset_mock()
        temp = controller.external_temperature
        assert temp == 10.0
        session.execute_api_call.assert_not_called()

    def test_external_temperature_returns_correct_value(self):
        controller, _ = self._make_controller()
        controller._weather_timestamp = 0.0
        assert controller.external_temperature == 8.5

    def test_solar_intensity_returns_correct_value(self):
        controller, _ = self._make_controller()
        controller._weather_timestamp = 0.0
        assert controller.solar_intensity == 42.0
