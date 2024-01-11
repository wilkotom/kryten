import base64
import hmac

from .session import Session
import json
import requests
import hashlib

from datetime import datetime, timezone
from time import time
from typing import Optional, Union, Tuple, Any


class SolisCloudSession(Session):
    __call_cache: dict[str, Tuple[int, dict[Any, Any]]]

    def __init__(self, key_id: str, key_secret: str, min_refresh: int = 60):
        self.__key_id: str = key_id
        self.__key_secret: str = key_secret
        self.__min_refresh = min_refresh
        self.__call_cache = {}
        inverter_list = self.execute_api_call("/v1/api/inverterList", {"pageNo": 1, "pageSize": 10}, "POST")
        self.__inverters = [i["id"] for i in inverter_list["data"]["page"]["records"]]

    @property
    def session_id(self) -> Optional[str]:
        return self.__key_id

    def execute_api_call(self, path: str, payload: Optional[dict[str, Union[bool, str, int]]],
                         method: str) -> dict:
        url = "https://www.soliscloud.com:13333" + path

        now = int(time())

        cached_val:  tuple[int, dict[str, dict[Any, Any]]] = self.__call_cache.get(url, (0, {}))
        if cached_val[0] + self.__min_refresh > now:
            return cached_val[1]

        request_body = json.dumps(payload)
        content_md5 = base64.b64encode(hashlib.md5(request_body.encode('utf-8')).digest()).decode('utf-8')
        timestamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_type = "application/json"
        sign = "POST\n" + content_md5 + "\n" + content_type + "\n" + \
               timestamp + "\n" + path

        hmac_val = hmac.new(self.__key_secret.encode("utf-8"), sign.encode("utf-8"), hashlib.sha1).digest()
        auth = base64.b64encode(hmac_val).decode("utf-8")

        request_headers = {
            "Content-Type": content_type,
            "Authorization": f"API {self.session_id}:{auth}",
            "Content-MD5": content_md5,
            "Date": timestamp,
        }

        try:
            resp = requests.post(url, headers=request_headers, data=request_body)
            self.__call_cache[url] = (now, resp.json())
        except json.JSONDecodeError:
            print(f"Failed to decode response {resp.status_code}: {resp.content}")
        except requests.exceptions.ConnectionError:
            print(f"Connection to {url} failed")
        finally:
            return self.__call_cache[url][1]

    @property
    def inverters(self) -> list[str]:
        return self.__inverters
