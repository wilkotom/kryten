import requests
from time import sleep
from threading import Thread

from .session import Session
from kryten.exceptions import LoginInvalidError, APIOperationNotImplementedError, UnexpectedResultError
from typing import Dict, List, Optional, Union, Callable, Any
from typing_extensions import Final

#  TODO: sort out this mess - parse the response object and construct
#  proper objects rather than using compound primitives
JsonResponseObject = Union[Dict[str, Any], Union[List[int], List[float], List[str], List[Dict[str, Any]]]]
HiveResponseObject = Dict[str, Union[str, Dict[str, str]]]
HiveRequestPayload = Optional[Dict[str, Union[bool, str, int]]]
HiveSchedule = Dict[str, List[Dict[str, Union[int, str, Dict[int, str]]]]]
HiveDeviceProperties = Dict[str, Union[str, int, List[str], bool]]
HiveProductList = List[Dict[str, Union[str, int, HiveDeviceProperties, HiveSchedule]]]
# HiveState = Dict[str, Union[str, Dict[str, Union[str, bool, HiveProductList]]]]
HiveState = JsonResponseObject


class HiveSession(Session):
    """Creates a session against the Centrica Hive Home Beekeeper API, providing methods that show available devices and
    performs requests against the API.
    """
    _request_headers: Dict[str, str] = {"Content-Type": "application/json",
                                        "Accept": "application/json",
                                        "User-Agent": "Kryten 2X4B 523P"}
    _username: str
    _password: str
    _debug: bool
    _session: Optional[str] = None
    _products: HiveProductList
    _beekeeper: Final[str] = "https://beekeeper-uk.hivehome.com/1.0"
    _hive_state: HiveState
    _stopping: int = False

    def __init__(self, username: str, password: str, debug: bool = False) -> None:
        self._username = username
        self._password = password
        self._debug = debug
        self.__create_session()

    def __create_session(self) -> None:
        login: HiveRequestPayload = {"username": self._username,
                                     "password": self._password}

        session_data: JsonResponseObject = self.execute_api_call(path="/global/login", payload=login, method="POST")

        if isinstance(session_data, dict) and "token" in session_data and isinstance(session_data["token"], str):
            try:
                self._session = session_data["token"]
            except KeyError:
                print(session_data.keys())
        elif not isinstance(session_data, dict):
            raise UnexpectedResultError(operation="login", result=str(session_data))
        else:
            raise LoginInvalidError("Hive", self._username)
        self._refresh_hive_state()

        self._background_refresh = Thread(target=self._periodic_state_refresh, args=(60,), daemon=True)
        self._background_refresh.start()

    def execute_api_call(self, path: str, payload: Optional[Dict[str, Union[bool, str, int]]] = None,
                         method: str = "GET") -> JsonResponseObject:
        """Executes the supplied REST call against the open Beekeeper session"""
        supported_ops: Dict[str, Callable[..., requests.Response]] = {"GET": requests.get,
                                                                      "POST": requests.post}

        if self.session_id is not None and "authorization" not in self._request_headers:
            self._request_headers["authorization"] = self.session_id

        if method not in supported_ops:
            raise APIOperationNotImplementedError(operation=method, url=f"{self._beekeeper}{path}")

        response = supported_ops[method](f"{self._beekeeper}{path}", json=payload, headers=self._request_headers)
        if self._debug:
            print(response.content)
        if response.status_code == 403 and \
                self._session is not None:
            try:
                self.__create_session()
                response = supported_ops[method](f"{self._beekeeper}{path}", json=payload,
                                                 headers=self._request_headers)
                if self._debug:
                    print(response.content)
            except LoginInvalidError as e:
                raise e

        parsed_response: Union[Dict[str, Any], List[Dict[str, Any]]] = response.json()
        return parsed_response

    @property
    def session_id(self) -> Optional[str]:
        """Contains the session ID of the current Beekeeper session"""
        return self._session

    @session_id.setter
    def session_id(self, sid: str) -> None:
        raise AttributeError("Session ID cannot be explicitly set")

    @property
    def devices(self) -> List[HiveDeviceProperties]:
        """Contains a list of devices that Beekeeper has supplied as being associated with the account"""
        if isinstance(self._hive_state, dict):
            return self._hive_state["products"]
        else:
            raise AttributeError("Hive State is not a singleton")

    @devices.setter
    def devices(self, props: List[HiveDeviceProperties]) -> None:
        raise AttributeError("Device List cannot be explicitly set")

    def _refresh_hive_state(self) -> None:

        hive_admin_session: HiveRequestPayload = {"token": str(self._session), "devices": True, "products": True,
                                                  "actions": True,
                                                  "homes": False}

        self._hive_state = self.execute_api_call(path="/auth/admin-login", payload=hive_admin_session, method="POST")

    def _periodic_state_refresh(self, duration: int) -> None:
        while not self._stopping:
            self._refresh_hive_state()
            sleep(duration)
