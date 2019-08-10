from typing import Optional, Union, Dict

def init( host: str, port: int = ..., prefix: Optional[str] = ..., timeout: int = 5, interval: Optional[int] = ...,
          queue_size: Optional[int] = ..., log_sends: bool = ..., protocol: str = ...,
          batch_size: int = ...): ...

def send( metric: str, value: Union[int, float], timestamp: float = ..., tags: Dict[str, str] = ...): ...