import requests
from time import sleep, time
import json
import logging
from threading import Thread

from .session import Session
from ...exceptions import LoginInvalidError, APIOperationNotImplementedError, UnexpectedResultError
from typing import Dict, List, Optional, Union, Callable, Any
from typing_extensions import Final

TadoResponse = Union[List[Dict[str, Any]], Dict[str, Any]]


class TadoSession(Session):
    """Creates a session against the Tado Smart Thermostat API, providing methods that show available devices and
    performs requests against the API.
    """
    _username: str
    _password: str
    _debug: bool
    _bearer_token: Optional[str] = None
    _refresh_token: Optional[str] = None
    _token_expiry: int = 0
    __logger: logging.Logger

    _tado_home_id: str
    _tado: Final[str] = 'https://my.tado.com/api/'
    _oath_url: Final[str] = 'https://auth.tado.com/oauth/token'
    _oath_client_secret: Final[str] = 'wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc'
    _maintain_session = Thread()

    def __init__(self, username: str, password: str, debug: bool = False, log_level: int = 25) -> None:
        self._username = username
        self._password = password
        self._debug = debug
        self.__create_session()
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(log_level)

    def __create_session(self) -> None:
        post_data = {'client_id': 'tado-web-app',
                     'grant_type': 'password',
                     'scope': 'home.user',
                     'username': self._username,
                     'password': self._password,
                     'client_secret': self._oath_client_secret}
        bearer_details = requests.post(self._oath_url, data=post_data)
        if bearer_details.status_code != 200:
            raise LoginInvalidError("Tado", self._username)
        bearer_json = bearer_details.json()
        self._token_expiry = bearer_json["expires_in"] + time()
        self._bearer_token = bearer_json["access_token"]
        self._refresh_token = bearer_json["refresh_token"]
        self._maintain_session = Thread(target=self.__renew_token, args=(), daemon=True)
        self._maintain_session.start()
        home_details = self.execute_api_call('v1/me')
        if isinstance(home_details, list):
            raise UnexpectedResultError("Multiple Homes returned")
        else:
            self._tado_home_id = str(home_details["homeId"])

    @property
    def session_id(self) -> Optional[str]:
        return self._bearer_token

    @property
    def home_id(self) -> Optional[str]:
        return self._tado_home_id

    def execute_api_call(self, path: str, payload: Optional[Dict[str, Union[bool, str, int]]] = None,
                         method: str = "GET") -> TadoResponse:

        supported_ops: Dict[str, Callable[..., requests.Response]] = {"GET": requests.get,
                                                                      "POST": requests.post}
        response = supported_ops[method](f"{self._tado}{path}", json=payload,
                                         headers={"Authorization": f"Bearer {self._bearer_token}"})

        parsed_response: Dict[str, Any] = response.json()
        return parsed_response

    def __renew_token(self) -> None:
        post_data = {'client_id': 'tado-web-app',
                     'grant_type': 'refresh_token',
                     'refresh_token': self._refresh_token,
                     'scope': 'home.user',
                     'client_secret': self._oath_client_secret}
        while True and self._refresh_token is not None:
            if self._token_expiry < time() + 60:
                renewal = requests.post(self._oath_url, post_data)
                if renewal.status_code != 200:
                    self.__create_session()
                else:
                    self._token_expiry = renewal.json()["expires_in"] + time()
            sleep(10)
