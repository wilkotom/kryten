from .metricsender import KrytenMetricSender
from ..exceptions import ImpossibleRequestError
from typing import Optional, Union
import statsd


class StatsDMetricSender(KrytenMetricSender):
    _statsd_client: Union[statsd.StatsClient, statsd.TCPStatsClient]

    def __init__(self, hostname: str, port: int = 8125, udp: bool = True, prefix: str = "kryten.data") -> None:
        if udp:
            self._statsd_client = statsd.StatsClient(host=hostname, port=port, prefix=prefix)
        else:
            print("Warning: TCP Statsd client in use. This is not thread safe.")
            self._statsd_client = statsd.TCPStatsClient(host=hostname, port=port, prefix=prefix)

    def send_metric(self, metric_name: str, value: Union[int, float, None], increment: bool = False,
                    tags: Optional[dict[str, str]] = None, metric_desc: Optional[str] = None) -> None:
        if increment:
            self._statsd_client.incr(metric_name, value)
        elif value is not None:
            self._statsd_client.gauge(metric_name, value)
        else:
            raise ImpossibleRequestError(f"StatsD {'counter' if increment else 'gauge'} {metric_name}", "None")
