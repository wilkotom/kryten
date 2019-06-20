from .light import SmartLights
from ...sessions.hive import HiveSession


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

    def list_lights(self):
        object_list = self._session.execute_api_call(path="/devices", headers={'Content-Length': '0'}).json
        return object_list
