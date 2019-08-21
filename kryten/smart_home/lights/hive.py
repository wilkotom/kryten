from .light import SmartLightController, SmartLightBulb
from ..sessions.hive import HiveSession
from ...exceptions import ImpossibleRequestError, OperationNotImplementedError
from ...metrics import KrytenMetricSender
from abc import abstractmethod
from typing import Dict, List, Union, Optional
from threading import Thread
from time import sleep


class HiveLightBulb(SmartLightBulb):
    """Provides a standard interface to all Hive smart bulbs"""
    _powered: bool
    _online: bool
    _session: HiveSession
    _bulb_id: str
    _name: str
    _action_thread: Thread
    _action_interrupt_semaphore: bool = False

    @property
    def uuid(self) -> str:
        return self._bulb_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def _presence(self) -> bool:
        return self._online

    @_presence.setter
    def _presence(self, state: bool) -> None:
        self._online = state

    @property
    @abstractmethod
    def brightness(self) -> int:
        pass

    @property
    @abstractmethod
    def power(self) -> bool:
        pass

    @abstractmethod
    def _update_attributes_from_hive(self, brightness: int, powered: bool, presence: bool):
        """Method provided to overwrite local state with remote (API-derived) state"""
        pass


class HiveCoolToWarmWhiteLightBulb(HiveLightBulb):
    """Object which provides control over a single Hive Cool to Warm White smart bulb"""

    @property
    def brightness(self) -> int:
        raise OperationNotImplementedError

    @brightness.setter
    def brightness(self, val: int) -> int:
        raise OperationNotImplementedError

    @property
    def power(self) -> bool:
        raise OperationNotImplementedError

    @power.setter
    def power(self, power_status) -> bool:
        raise OperationNotImplementedError

    def sunrise(self, period: int) -> None:
        raise OperationNotImplementedError

    def sunset(self, period: int) -> None:
        raise OperationNotImplementedError

    def _update_attributes_from_hive(self, brightness: int, powered: bool, presence: bool):
        raise OperationNotImplementedError


class HiveColourLightBulb(HiveLightBulb):
    """Object which provides control over a single Hive Colour smart bulb"""

    @property
    def brightness(self) -> int:
        raise OperationNotImplementedError

    @brightness.setter
    def brightness(self, val: int) -> int:
        raise OperationNotImplementedError

    @property
    def power(self) -> bool:
        raise OperationNotImplementedError

    @power.setter
    def power(self, power_status) -> bool:
        raise OperationNotImplementedError

    def sunrise(self, period: int) -> None:
        raise OperationNotImplementedError

    def sunset(self, period: int) -> None:
        raise OperationNotImplementedError

    def _update_attributes_from_hive(self, brightness: int, powered: bool, presence: bool):
        raise OperationNotImplementedError


class HiveWarmWhiteBulb(HiveLightBulb):
    """Object which provides control over a single Hive Warm White smart bulb"""
    _brightness: int

    def __init__(self, session: HiveSession, uuid: str, desc: str, presence: bool) -> None:
        self._session = session
        self._bulb_id = uuid
        self._name = desc
        self._action_thread = Thread()
        for device in session.devices:
            if device["id"] == uuid and isinstance(device, dict) and isinstance(device["state"], dict):
                self._brightness = device["state"]["brightness"]
                self._powered = device["state"]["status"] == "ON"
                self._presence = presence

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, val: int):
        if not 0 < val <= 100:
            raise ImpossibleRequestError(operation="Bulb Brightness", val=str(val))

        self._session.execute_api_call(path="/nodes/warmwhitelight/" + self._bulb_id, method="POST",
                                       payload={"brightness": val})
        self._brightness = val

    def sunrise(self, period: int = 0) -> None:
        while self._action_thread.is_alive():
            if not self._action_interrupt_semaphore:
                self._action_interrupt_semaphore = True
            sleep(1)
        if self.brightness != 1:
            self.brightness = 1
        if self.power is False:
            self.power = True

        self._action_thread = Thread(target=self._fade, args=(1, 100, period))
        self._action_thread.start()

    def sunset(self, period: int = 0) -> None:

        while self._action_thread.is_alive():
            if not self._action_interrupt_semaphore:
                self._action_interrupt_semaphore = True
            sleep(1)

        self._action_thread = Thread(target=self._fade, args=(self.brightness, 0, period))
        self._action_thread.start()

    def _fade(self, start: int, end: int, period: int, step: int = 1) -> None:
        power_down = False
        if start == end:
            return
        if end == 0:
            power_down = True
            end = 1
        snooze = period / ((start - end) * step)
        if start > end:
            step = -step

        for i in range(start, end + step, step):
            if self._action_interrupt_semaphore:
                self._action_interrupt_semaphore = False
                return
            self.brightness = i
            sleep(snooze)
        if power_down:
            self.power = False

    @property
    def power(self) -> bool:
        return self._powered

    @power.setter
    def power(self, power_status: bool) -> None:
        self._session.execute_api_call(path="/nodes/warmwhitelight/" + self._bulb_id, method="POST",
                                       payload={"status": "ON" if power_status else "OFF"})
        self._powered = power_status

    def _update_attributes_from_hive(self, brightness: int, powered: bool, presence: bool) -> None:
        self._brightness = brightness
        self._powered = powered
        self._presence = presence


HiveSupportedLightBulb = Union[HiveWarmWhiteBulb, HiveCoolToWarmWhiteLightBulb, HiveColourLightBulb]


class HiveSmartLightController(SmartLightController):
    _session: HiveSession
    _bulbs: Dict[str, HiveSupportedLightBulb] = {}

    def __init__(self, session: HiveSession, metric_sender: Optional[KrytenMetricSender] = None) -> None:
        self._session = session
        self._generate_light_list()
        updater_thread = Thread(target=self._updater_thread, args=(20,))
        updater_thread.start()
        if metric_sender is not None:
            metrics_thread = Thread(target=self.__send_metrics, args=(metric_sender, 20))
            metrics_thread.start()

    def bulb(self, light_id: str) -> HiveSupportedLightBulb:
        return self._bulbs[light_id]

    def brightness(self, light_id: str, brightness: int = 0) -> None:
        if not 0 < brightness <= 100:
            raise ImpossibleRequestError(operation="Bulb Brightness", val=str(brightness))
        if light_id in self._bulbs.keys():
            self.bulb(light_id).brightness = brightness
        else:
            raise ImpossibleRequestError(operation=f"Bulb Brightness for unknown bulb {light_id}", val=f"{brightness}")

    def _generate_light_list(self) -> None:
        object_list = self._session.execute_api_call(path="/devices")
        for bulb in filter(lambda x: "type" in x and x["type"] == "warmwhitelight", object_list):
            if isinstance(bulb, dict):
                self._bulbs[bulb["id"]] = HiveWarmWhiteBulb(self._session, str(bulb["id"]), str(bulb["state"]["name"]),
                                                            bulb["props"]["online"])

    def list_lights(self) -> List[Dict[str, str]]:
        return [{"id": x[0], "name": x[1].name} for x in self._bulbs.items()]

    def _updater_thread(self, interval):
        while True:
            for device in self._session._hive_state["products"]:
                if device["id"] in self._bulbs:
                    self._bulbs[device["id"]]._update_attributes_from_hive(device["state"]["brightness"],
                                                                           device["state"]["status"] == "ON",
                                                                           device["props"]["online"])
            sleep(interval)

    def __send_metrics(self, metric_sender: KrytenMetricSender, interval: int = 20):
        while True:
            for device in self._bulbs.values():
                device_name = device.name.replace(u"\u2018", "'").replace(u"\u2019", "'")
                metric_sender.send_metric(f"Bulb.{device_name}.brightness", device.brightness)
                metric_sender.send_metric(f"Bulb.{device_name}.power", 1 if device.power else 0)
            sleep(interval)