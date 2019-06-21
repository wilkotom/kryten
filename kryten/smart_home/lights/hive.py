from .light import SmartLightController
from ...sessions.hive import HiveSession
from ...exceptions import ImpossibleRequestError

from typing import Dict, List


class HiveSmartLightController(SmartLightController):
    _session: HiveSession

    def __init__(self, session: HiveSession) -> None:
        self._session = session

    def illuminate(self) -> bool:
        return False

    def extinguish(self, light_id: str) -> bool:
        return False

    def brightness(self, light_id: str, brightness: int = 0) -> None:
        if not 0 < brightness <= 100:
            raise ImpossibleRequestError(operation="Bulb Brightness", val=(brightness))
        self._session.execute_api_call(path="/nodes/warmwhitelight/" + light_id, method="POST",
                                       payload={"brightness": brightness})

    def list_lights(self) -> List[Dict[str, str]]:
        object_list = self._session.execute_api_call(path="/devices")
        output_list: List = []
        for object in object_list:
            if object['type'] == 'warmwhitelight':
                output_list.append({'id': object['id'], 'name': object['state']['name']})

        return output_list
