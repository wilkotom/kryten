import requests
import json

from .session import Session
from ..exceptions import LoginInvalid, APIOperationNotImplemented
from typing import Dict, List, Optional, Union


class HiveSession(Session):
    _request_headers: Dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json",
                                        "User-Agent": "Kryten 2X4B 523P"}
    _username: str
    _password: str
    _session: Optional[str] = None
    _beekeeper: str = 'https://beekeeper.hivehome.com/1.0'

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self.__create_session(self._username, self._password)

    def __create_session(self, username: str, password: str) -> None:
        login: Dict[str, str] = {"username": username,
                                 "password": password}

        session_data = self.execute_api_call(path='/global/login', payload=login, method='POST',
                                             headers={"Content-Type": "application/json", "Accept": "application/json",
                                                      "User-Agent": "Kryten 2X4B 523P"})

        if session_data.status_code != 200:
            print(session_data.json())
            raise LoginInvalid("Hive", username)
        self._session = session_data.json()['token']

    def execute_api_call(self, path: str, payload: Optional[Dict[str, str]] = None, method: str = "GET",
                         headers: Dict[str, str] = {}) -> List[Dict[str, Union[str, Dict[str, str]]]]:
        supported_ops = {'GET': requests.get,
                         'POST': requests.post}

        if self.session_id is not None and "authorization" not in self._request_headers:
            self._request_headers['authorization'] = self.session_id

        if method not in supported_ops:
            raise APIOperationNotImplemented(operation=method, url=f"{self._beekeeper}{path}")
        response = supported_ops[method](f"{self._beekeeper}{path}", json=payload, headers=self._request_headers)
        if response.status_code != 200:
            print(response.request.method)
            print(response.request.headers)
            print(response.status_code, response.content)
            raise LoginInvalid(f"{self._beekeeper}{path}")
        return response

    @property
    def session_id(self) -> str:
        return self._session

    @session_id.setter
    def session_id(self, sid: str) -> None:
        raise AttributeError("Session ID cannot be explicitly set")
