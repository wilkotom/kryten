from ..sessions.tado import TadoSession, TadoResponse
from .thermostat import ThermostatController, ThermostatZone
from typing import List, Dict, Union
from typing_extensions import Final
from ...exceptions import UnexpectedResultError
from time import time
import json


def weather_updater(func):
    def update_weather(obj):
        now = time()
        if obj._weather_timestamp + obj._weather_refresh < now:
            weather_details = obj._tado_session.execute_api_call(
                f'v2/homes/{obj._tado_session.home_id}/weather')
            obj._solar_intensity = weather_details['solarIntensity']['percentage']
            obj._outside_temperature = weather_details['outsideTemperature']['celsius']
            obj._weather_timestamp = now
        return func(obj)

    return update_weather


class TadoThermostatZone(ThermostatZone):

    _session: TadoSession
    __zone_id: Union[int, str]
    __state_timestamp: float = 0
    _power: bool
    _internal_temperature: float
    _target_temperature: float
    _humidity: float
    _min_refresh: Final[int]  # Don't hammer the API more than once in a period( default: 60s)

    def __init__(self, session: TadoSession, zone_id: Union[int, str], min_refresh: int = 60) -> None:
        self._session = session
        self.__zone_id = zone_id
        self._min_refresh = min_refresh
        self.__update_current_state()

    def __update_current_state(self):
        now = time()
        if self.__state_timestamp + self._min_refresh < now:
            state = self._session.execute_api_call(f'v2/homes/{self._session.home_id}/zones/{self.__zone_id}/state')
            if isinstance(state, list):
                raise UnexpectedResultError("List returned by Tado zone details call")
            else:
                try:
                    self._humidity = state['sensorDataPoints']['humidity']['percentage']
                    self._internal_temperature = state['sensorDataPoints']['insideTemperature']['celsius']
                    self._power = True if state['setting']['power'] == 'ON' else False
                    self._target_temperature = state['setting']['temperature']['celsius']
                    self.__state_timestamp = now
                except KeyError as error:
                    print("ERROR: Response did not contain expected fields")
                    print(f"Response was: {json.dumps(state, indent=2)}")

    @property
    def current_temperature(self) -> float:
        self.__update_current_state()
        return self._internal_temperature

    @property
    def humidity(self) -> float:
        self.__update_current_state()
        return self._humidity

    @property
    def target_temperature(self) -> float:
        self.__update_current_state()
        return self._target_temperature


class TadoThermostatController(ThermostatController):
    _tado_session: TadoSession
    _zones: Dict[Union[int, str], TadoThermostatZone] = {}
    _weather_refresh: Final[int]
    _weather_timestamp: float = 0.0
    _solar_intensity: float
    _outside_temperature: float

    def __init__(self, session: TadoSession, weather_refresh: int = 900) -> None:
        self._tado_session = session
        self._weather_refresh = weather_refresh
        for zone in self._get_zone_list():
            self._zones[zone["id"]] = TadoThermostatZone(self._tado_session, zone["id"])

    def _get_zone_list(self) -> List[Dict[Union[int, str], str]]:
        zone_details = self._tado_session.execute_api_call(f'v2/homes/{self._tado_session.home_id}/zones')
        if not isinstance(zone_details, list):
            raise UnexpectedResultError("Singleton returned when fetching zone list")

        return [{'id': z["id"], 'name': z["name"]}
                for z in filter(lambda z: z["type"] == "HEATING", zone_details)]

    @property  # type: ignore
    @weather_updater
    def external_temperature(self) -> float:
        return self._outside_temperature

    @property # type: ignore
    @weather_updater
    def solar_intensity(self) -> float:
        return self._solar_intensity

    @property
    def zones(self) -> List[Dict[Union[int, str], str]]:
        return self._get_zone_list()

    def zone(self, zone_id: int) -> TadoThermostatZone:
        return self._zones[zone_id]

