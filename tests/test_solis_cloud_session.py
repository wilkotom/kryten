import base64
import hashlib
import json

import pytest
import requests as req
from unittest.mock import patch, MagicMock

from kryten.smart_home.sessions.solis_cloud import SolisCloudSession


INVERTER_LIST_RESPONSE = {
    "data": {
        "page": {
            "records": [
                {"id": "inverter-001"},
                {"id": "inverter-002"},
            ]
        }
    }
}


def make_mock_response(data: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.status_code = 200
    return mock_resp


def make_session(key_id="key123", key_secret="secret456", min_refresh=60):
    """Create a SolisCloudSession with the inverterList call mocked."""
    with patch("requests.post") as mock_post:
        mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
        session = SolisCloudSession(key_id, key_secret, min_refresh=min_refresh)
    return session


class TestSolisCloudSessionInit:
    def test_fetches_inverter_list_on_init(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            session = SolisCloudSession("key123", "secret456")
        assert session.inverters == ["inverter-001", "inverter-002"]
        assert mock_post.call_count == 1

    def test_session_id_returns_key_id(self):
        session = make_session(key_id="mykey")
        assert session.session_id == "mykey"


class TestSolisCloudSessionCaching:
    def test_second_call_within_min_refresh_uses_cache(self):
        # min_refresh=60, so a second call immediately after should hit the cache
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            session = SolisCloudSession("key123", "secret456", min_refresh=60)
            mock_post.reset_mock()
            result = session.execute_api_call(
                "/v1/api/inverterList", {"pageNo": 1, "pageSize": 10}, "POST"
            )
        assert mock_post.call_count == 0
        assert result == INVERTER_LIST_RESPONSE

    def test_call_after_min_refresh_makes_new_request(self):
        # min_refresh=0 means every call is considered stale
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            session = SolisCloudSession("key123", "secret456", min_refresh=0)
            mock_post.reset_mock()
            session.execute_api_call(
                "/v1/api/inverterList", {"pageNo": 1, "pageSize": 10}, "POST"
            )
        assert mock_post.call_count == 1


class TestSolisCloudSessionErrorHandling:
    def test_connection_error_returns_last_cached_value(self):
        # First call succeeds and populates the cache
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            session = SolisCloudSession("key123", "secret456", min_refresh=0)
            # Now force a ConnectionError
            mock_post.side_effect = req.exceptions.ConnectionError("refused")
            result = session.execute_api_call(
                "/v1/api/inverterList", {"pageNo": 1, "pageSize": 10}, "POST"
            )
        assert result == INVERTER_LIST_RESPONSE


class TestSolisCloudSessionHeaders:
    def test_authorization_header_starts_with_api_and_key_id(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            SolisCloudSession("testkey", "testsecret")
            headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"].startswith("API testkey:")

    def test_content_md5_matches_body(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            SolisCloudSession("testkey", "testsecret")
            headers = mock_post.call_args[1]["headers"]
            body = mock_post.call_args[1]["data"]
        expected_md5 = base64.b64encode(
            hashlib.md5(body.encode("utf-8")).digest()
        ).decode("utf-8")
        assert headers["Content-MD5"] == expected_md5

    def test_content_type_is_json(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response(INVERTER_LIST_RESPONSE)
            SolisCloudSession("testkey", "testsecret")
            headers = mock_post.call_args[1]["headers"]
        assert headers["Content-Type"] == "application/json"
