from abc import ABC, abstractmethod
from typing import Union


class KrytenMetricSender(ABC):

    @abstractmethod
    def send_metric(self, metric_name: str, value: Union[int, float], increment: bool = False) -> None:
        pass
