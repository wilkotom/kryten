import json
from threading import Thread
from time import sleep
from typing import Optional

from ..sessions import SolisCloudSession
from .inverter import SolarPowerInverter
from ...metrics import KrytenMetricSender


class SolisSolarPowerInverter(SolarPowerInverter):
    _session: SolisCloudSession
    _inverter_id: int

    def __init__(self, session: SolisCloudSession, inverter_id: int,
                 metric_sender: Optional[KrytenMetricSender] = None):
        self._session = session
        self._inverter_id = inverter_id
        if metric_sender is not None:
            self.__send_metrics(metric_sender)

    @property
    def generation(self) -> float:
        try:
            inverter_details = self._session.execute_api_call(
                "/v1/api/inverterDetail", {"id": self._inverter_id}, "POST")
            return inverter_details["data"]["pac"]
        except json.JSONDecodeError:
            return None

    @property
    def battery_discharge_rate(self) -> float:
        return 0.0

    @property
    def battery_level(self) -> float:
        inverter_details = self._session.execute_api_call(
            "/v1/api/inverterDetail", {"id": self._inverter_id}, "POST")
        return inverter_details["data"]["batteryCapacitySoc"]

    @property
    def export_rate(self) -> float:
        return 0.0

    def __send_metrics(self, metric_sender):
        self._maintain_session = Thread(target=self.__gather_metrics, args=(metric_sender,), daemon=True)
        self._maintain_session.start()

    def __gather_metrics(self, metric_sender: KrytenMetricSender) -> None:
        while True:
            metric_sender.send_metric(f"inverter_generation", self.generation,
                                      tags={"name": f"Inverter{self._inverter_id}"},metric_desc="Generation (KW)")
            metric_sender.send_metric(f"inverter_batterySoc", self.battery_level,
                                      tags={"name": f"Inverter{self._inverter_id}"}, metric_desc="Battery Charge (%)")
            sleep(300)
