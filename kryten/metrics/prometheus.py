from threading import Thread

from .metricsender import KrytenMetricSender
from typing import Union, Optional
import prometheus_client


class PrometheusMetricSender(KrytenMetricSender):
    __prefix: str
    __recorders: dict[str, prometheus_client.Gauge]

    def __init__(self, hostname: str, prefix: str = "kryten.data") -> None:
        prometheus_client.start_http_server(port=8001)
        self.__prefix = prefix
        self.__recorders = {}

    def send_metric(self, metric_name: str, value: Union[int, float], increment: bool = False,
                    tags: Optional[dict[str, str]] = None,
                    metric_desc: Optional[str] = None) -> None:
        if tags is None:
            tags = {}
        prom_metric_name = f"kryten_{metric_name}"
        if metric_desc is None:
            metric_desc = prom_metric_name

        if prom_metric_name not in self.__recorders:
            self.__recorders[prom_metric_name] = prometheus_client.Gauge(prom_metric_name,
                                                                         metric_desc, tags.keys())

        if increment:
            self.__recorders[prom_metric_name].labels(**tags).inc(value)
        else:
            self.__recorders[prom_metric_name].labels(**tags).set(value)
