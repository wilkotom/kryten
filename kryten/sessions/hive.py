import requests
import json

from .session import Session
from ..exceptions import LoginInvalid
from typing import Dict

class HiveSession(Session):
    _request_headers: Dict[str, str] = {"Content-Type": "application/vnd.alertme.zoo-6.6+json",
                            "Accept": "application/vnd.alertme.zoo-6.6+json",
                            "X-Omnia-Client": "krytenx"}
    _username: str
    _password: str
    _session: str

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self.__create_session(self._username, self._password)

    def __create_session(self, username: str, password: str) -> None:
        login = json.dumps({
            "sessions": [{
                "username": f"{username}",
                "password": f"{password}",
                "caller": "WEB"
            }]
        })
        session_data = requests.post("https://api.prod.bgchprod.info:443/omnia/auth/sessions", login,
                                     headers=self._request_headers)
        if session_data.status_code != 200:
            print(session_data.json())
            raise LoginInvalid("Hive", username)
        self._session = session_data.json()['sessions'][0]['sessionId']

    @property
    def session_id(self) -> str:
        return self._session

    @session_id.setter
    def session_id(self, sid: str) -> None:
        raise AttributeError("Session ID cannot be explicitly set")

