from .light import SmartLights
from ...sessions.hive import HiveSession

from typing import Dict, List

class HiveSmartLights(SmartLights):

    _session: HiveSession

    def __init__(self, session: HiveSession) -> None:
        self._session = session

    def illuminate(self) -> bool:
        return False

    def extinguish(self, light_id: str) -> bool:
        return False

    def brightness(self, light_id: str) -> None:
        return None

    def list_lights(self) -> List[Dict[str, str]]:
        object_list = self._session.execute_api_call(path="/devices").json()
        output_list: List = []
        for object in object_list:
            if object['type'] == 'warmwhitelight':
                output_list.append({'id': object['id'], 'name': object['state']['name']})

        return output_list
