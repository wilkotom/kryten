from ..sessions.tado import TadoSession, TadoResponse
from .thermostat import ThermostatController, ThermostatZone
from typing import List, Dict, Callable, Any
from ...exceptions import UnexpectedResultError


class TadoThermostatZone(ThermostatZone):

    _session: TadoSession
    __zone_id: int
    _power: bool
    _internal_temperature: float
    _target_temperature: float
    _humidity: float

    def __init__(self, session: TadoSession, zone_id: int) -> None:
        self._session = session
        self.__zone_id - zone_id

    def __get_current_state(self):
        state = self._session.execute_api_call(f'v2/homes/{self._session.home_id}/zones/{self.__zone_id}/state')
        if isinstance(state, list):
            raise UnexpectedResultError("List returned by Tado zone details call")
        else:
            self._humidity = state['sensorDataPoints']['humidity']['percentage']
            self._internal_temperature = state['sensorDataPoints']['insideTemperature']['celsius']
            self._internal_temperature = True if state['setting']['power'] == 'ON' else False

    @property
    def current_temperature(self) -> float:
        return self._internal_temperature


class TadoThermostatController(ThermostatController):
    _tado_session: TadoSession
    _zones: List[Dict[str, str]]

    def __init__(self, session: TadoSession) -> None:
        self._tado_session = session
        self._get_zone_list()

    def _get_zone_list(self) -> None:
        zone_details = self._tado_session.execute_api_call(f'v2/homes/{self._tado_session.home_id}/zones')
        if isinstance(zone_details, list):
            self._zones = [{'id': z["id"], 'name': z["name"]}
                           for z in filter(lambda z: z["type"] == "HEATING", zone_details)]
        else:
            raise UnexpectedResultError("Singleton returned when fetching zone list")

    def list_zones(self) -> List[Dict[str, str]]:
        self._get_zone_list()
        return self._zones

