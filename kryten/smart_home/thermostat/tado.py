from ..sessions.tado import TadoSession
from ...metrics import KrytenMetricSender
from .thermostat import ThermostatController, ThermostatZone
from typing import List, Dict, Union, Callable, Optional
from typing_extensions import Final
from ...exceptions import UnexpectedResultError
from time import time, sleep
from threading import Thread

import json


def weather_updater(func: Callable[[ThermostatController], float]) -> Callable[[ThermostatController], float]:
    def update_weather(obj):
        now = time()
        if obj._weather_timestamp + obj._weather_refresh < now:
            weather_details = obj._tado_session.execute_api_call(
                f'v2/homes/{obj._tado_session.home_id}/weather')
            try:
                obj._solar_intensity = weather_details['solarIntensity']['percentage']
                obj._outside_temperature = weather_details['outsideTemperature']['celsius']
                obj._weather_timestamp = now
            except KeyError:
                print(f"Did not understand weather output: {weather_details}")
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

    def __init__(self, session: TadoSession, zone_id: Union[int, str], min_refresh: int = 300) -> None:
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
                    self._target_temperature = self._internal_temperature if state['setting'][
                                                                                 'temperature'] is None else \
                        state['setting']['temperature']['celsius']
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
    _zone_list: List[Dict[Union[int, str], str]] = []
    _weather_refresh: Final[int]
    _weather_timestamp: float = 0.0
    _solar_intensity: float
    _outside_temperature: float
    _metrics_thread: Thread = Thread()

    def __init__(self, session: TadoSession, metric_sender: Optional[KrytenMetricSender] = None,
                 weather_refresh: int = 300) -> None:
        self._tado_session = session
        self._weather_refresh = weather_refresh
        for zone in self._get_zone_list():
            self._zones[zone["id"]] = TadoThermostatZone(self._tado_session, zone["id"])
        if metric_sender is not None:
            self.__send_metrics(metric_sender)

    def _get_zone_list(self) -> List[Dict[Union[int, str], str]]:
        if not self._zone_list:
            zone_details = self._tado_session.execute_api_call(f'v2/homes/{self._tado_session.home_id}/zones')
            if not isinstance(zone_details, list):
                raise UnexpectedResultError("Singleton returned when fetching zone list")

            self._zone_list = [{'id': z["id"], 'name': z["name"]}
                               for z in filter(lambda z: z["type"] == "HEATING", zone_details)]

        return self._zone_list

    @property  # type: ignore
    @weather_updater
    def external_temperature(self) -> float:
        return self._outside_temperature

    @property  # type: ignore
    @weather_updater
    def solar_intensity(self) -> float:
        return self._solar_intensity

    @property
    def zones(self) -> List[Dict[Union[int, str], str]]:
        return self._get_zone_list()

    def zone(self, zone_id: Union[str, int]) -> TadoThermostatZone:
        return self._zones[zone_id]

    def __send_metrics(self, metric_sender):
        self._maintain_session = Thread(target=self.__gather_metrics, args=(metric_sender,), daemon=True)
        self._maintain_session.start()

    def __gather_metrics(self, metric_sender: KrytenMetricSender) -> None:
        while True:
            for zone in self.zones:
                zone_name = zone['name']
                zone_details = self.zone(zone['id'])
                metric_sender.send_metric(f"thermostat_target", zone_details.target_temperature,
                                          tags={"zone": zone_name, "home_id": f"{self._tado_session.home_id}"},
                                          metric_desc="Target Temperature")
                metric_sender.send_metric(f"thermostat_now", zone_details.current_temperature,
                                          tags={"zone": zone_name, "home_id": f"{self._tado_session.home_id}"},
                                          metric_desc="Current Temperature")
                metric_sender.send_metric(f"thermostat_humidity", zone_details.humidity,
                                          tags={"zone": zone_name, "home_id": f"{self._tado_session.home_id}"},
                                          metric_desc="Humidity")
            metric_sender.send_metric("thermostat_external_temp", self.external_temperature,
                                      tags={"home_id": f"{self._tado_session.home_id}"},
                                      metric_desc="External Temperature")
            metric_sender.send_metric("thermostat_solar_intensity", self.solar_intensity,
                                      tags={"home_id": f"{self._tado_session.home_id}"}, metric_desc="Solar Intensity")
            sleep(300)
