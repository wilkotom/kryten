from abc import ABC, abstractmethod
from typing import Union, Optional


class KrytenMetricSender(ABC):

    @abstractmethod
    def send_metric(self, metric_name: str, value: Union[int, float], increment: bool = False,
                    tags: Optional[dict[str, str]] = None, metric_desc: Optional[str] = None) -> None:
        pass
