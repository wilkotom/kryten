from .metricsender import KrytenMetricSender
from typing import Union, Optional
import graphyte


class GraphiteMetricSender(KrytenMetricSender):

    def __init__(self, hostname: str, prefix: str = "kryten.data") -> None:
        graphyte.init(host=hostname, prefix=prefix, interval=30)

    def send_metric(self, metric_name: str, value: Union[int, float], increment: bool = False,
                    tags: Optional[dict[str, str]] = None, metric_desc: Optional[str] = None) -> None:

        graphyte.send(metric_name, value)




