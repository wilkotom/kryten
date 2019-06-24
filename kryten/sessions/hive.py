import requests

from kryten.sessions.session import Session
from kryten.exceptions import LoginInvalidError, APIOperationNotImplementedError
from typing import Dict, List, Optional, Union, Callable, Any
from typing_extensions import Final

HiveResponseObject = Dict[str, Union[str, Dict[str, str]]]
HiveSchedule = Dict[str, List[Dict[str, Union[int, str, Dict[int, str]]]]]
HiveDeviceProperties = Dict[str, Union[str, int, List[str], bool]]
HiveProductList = List[Dict[str, Union[str, int, HiveDeviceProperties, HiveSchedule]]]
HiveState = Dict[str, Union[str, Dict[str, Union[str, bool, HiveProductList]]]]


class HiveSession(Session):

    _request_headers: Dict[str, str] = {"Content-Type": "application/json", 
                                        "Accept": "application/json",
                                        "User-Agent": "Kryten 2X4B 523P"}
    _username: str
    _password: str
    _session: Optional[str] = None
    _products: HiveProductList
    _beekeeper: Final[str] = 'https://beekeeper-uk.hivehome.com/1.0'
    _hive_state: HiveState

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self.__create_session(self._username, self._password)

    def __create_session(self, username: str, password: str) -> None:
        login: Dict[str, str] = {"username": username,
                                 "password": password}

        session_data: Union[HiveResponseObject,List[HiveResponseObject]] = self.execute_api_call(path='/global/login', payload=login, method='POST',
                                             headers={"Content-Type": "application/json", "Accept": "application/json",
                                                      "User-Agent": "Kryten 2X4B 523P"})

        if isinstance(session_data, dict) and 'token' in session_data and isinstance(session_data['token'], str):
            try:
                self._session = session_data["token"]
            except KeyError:
                print(session_data.keys())
        else:            
            raise LoginInvalidError("Hive", username)

        hive_admin_session = {"token": self._session, "devices": True, "products": True, "actions": True,
                              "homes": False}
        self._hive_state: HiveState = self.execute_api_call(path='/auth/admin-login', payload=hive_admin_session, method='POST',
                headers={"Content-Type": "application/json", "Accept": "application/json",
                   "User-Agent": "Kryten 2X4B 523P"})

    def execute_api_call(self, path: str, payload: Optional[Dict[str, str]] = None, method: str = "GET",
                         headers: Dict[str, str] = {}) -> Union[HiveResponseObject,List[HiveResponseObject]]:
        supported_ops: Dict[str, Callable[..., requests.Response]] = {'GET': requests.get,
                         'POST': requests.post}

        if self.session_id is not None and "authorization" not in self._request_headers:
            self._request_headers['authorization'] = self.session_id

        if method not in supported_ops:
            raise APIOperationNotImplementedError(operation=method, url=f"{self._beekeeper}{path}")
        response = supported_ops[method](f"{self._beekeeper}{path}", json=payload, headers=self._request_headers)
        if response.status_code != 200:
            raise LoginInvalidError(f"{self._beekeeper}{path}")
        return response.json()

    @property
    def session_id(self) -> Optional[str]:
        return self._session

    @session_id.setter
    def session_id(self, sid: str) -> None:
        raise AttributeError("Session ID cannot be explicitly set")

    @property
    def devices(self) -> List[HiveDeviceProperties]:
        return self._hive_state['products']

    @devices.setter
    def devices(self) -> None:
        raise AttributeError("Device List cannot be explicitly set")

