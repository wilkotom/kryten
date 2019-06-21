from .light import SmartLightController, SmartLightBulb
from ...sessions.hive import HiveSession
from ...exceptions import ImpossibleRequestError

from typing import Dict, List


class HiveWarmWhiteBulb(SmartLightBulb):

    _brightness: int
    _powered: bool
    _session: str
    _bulb_id: str
    _name: str

    def __init__(self, session: HiveSession, uuid: str, desc: str) -> None:
        self._session = session
        self._bulb_id = uuid
        self._name = desc

    @property
    def uuid(self) -> str:
        return self._bulb_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, val: int) -> int:
        if not 0 < val <= 100:
            raise ImpossibleRequestError(operation="Bulb Brightness", val=str(val))
        self._session.execute_api_call(path="/nodes/warmwhitelight/" + self._bulb_id, method="POST",
                                       payload={"brightness": val})
        self._brightness = val
        return val

    @property
    def power(self) -> bool:
        return self._powered

    @power.setter
    def power(self, val: bool):
        raise ImpossibleRequestError(operation="Bulb Power", val="on" if val else "off")

    def sunrise(self) -> bool:
        pass

    def sunset(self) -> bool:
        pass


class HiveSmartLightController(SmartLightController):
    _session: HiveSession
    _bulbs: Dict[str, HiveWarmWhiteBulb] = {}

    def __init__(self, session: HiveSession) -> None:
        self._session = session
        self._generate_light_list()

    def illuminate(self) -> bool:
        return False

    def extinguish(self, light_id: str) -> bool:
        return False

    def brightness(self, light_id: str, brightness: int = 0) -> None:
        if not 0 < brightness <= 100:
            raise ImpossibleRequestError(operation="Bulb Brightness", val=str(brightness))
        self._session.execute_api_call(path="/nodes/warmwhitelight/" + light_id, method="POST",
                                       payload={"brightness": brightness})

    def _generate_light_list(self) -> None:
        object_list = self._session.execute_api_call(path="/devices")
        for object in object_list:
            if object['type'] == 'warmwhitelight':
                self._bulbs[object['id']] = HiveWarmWhiteBulb(self._session, object['id'], object['state']['name'])

    def list_lights(self) -> List[Dict[str, str]]:
        return [{'id': x[0], 'name': x[1].name} for x in self._bulbs.items()]
