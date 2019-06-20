import typing
import requests
import json

from .session import Session
from ..exceptions import LoginInvalid


class HiveSession(Session):
    __request_headers: typing.Dict[str, str] = {"Content-Type": "application/vnd.alertme.zoo-6.6+json",
                            "Accept": "application/vnd.alertme.zoo-6.1+json",
                            "X-Omnia-Client": "krytenx"}

    session_id: str = None
    __username: str = None
    __password: str = None

    def __init__(self, username: str, password: str):
        self.__username = username
        self.__password = password
        self.__create_session(self.__username, self.__password)

    def __create_session(self, username: str, password: str):
        login = json.dumps({
            "sessions": [{
                "username": f"{username}",
                "password": f"{password}",
                "caller": "WEB"
            }]
        })
        session_data = requests.post("https://api.prod.bgchprod.info:443/omnia/auth/sessions", login,
                                     headers=self.__request_headers)
        if session_data.status_code != 200:
            print(session_data.json())
            raise LoginInvalid("Hive", username)
        self.session_id = session_data.json()['sessions'][0]['sessionId']

