from ..sessions.tado import TadoSession
from .thermostat import ThermostatController
from typing import List, Dict


class TadoThermostatController(ThermostatController):
    _tado_session: TadoSession
    _zones: List[Dict[str, str]]

    def __init__(self, session: TadoSession) -> None:
        self._tado_session = session
        self._get_zone_list()

    def _get_zone_list(self):
        self._zones = self._tado_session.execute_api_call(f'v2/homes/{self._tado_session.home_id}/zones')

    def list_zones(self) -> List[Dict[str, str]]:
        self._get_zone_list()
        return self._zones

