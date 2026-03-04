import pytest
import requests as req
from json.decoder import JSONDecodeError
from unittest.mock import patch, MagicMock

from kryten.smart_home.sessions.tado import TadoSession
from kryten.exceptions import LoginInvalidError


OAUTH_SUCCESS = {
    "access_token": "bearer-token-123",
    "refresh_token": "refresh-token-456",
    "expires_in": 3600,
}
HOME_DETAILS = {"homeId": 12345}


def make_mock_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    return mock


def make_session():
    """Create a TadoSession with all HTTP mocked and no background threads."""
    with patch("kryten.smart_home.sessions.tado.Thread"), \
         patch("requests.post") as mock_post, \
         patch("requests.get") as mock_get:
        mock_post.return_value = make_mock_response(OAUTH_SUCCESS)
        mock_get.return_value = make_mock_response(HOME_DETAILS)
        session = TadoSession("user@example.com", "password123")
    return session


class TestTadoSessionLogin:
    def test_successful_login_stores_bearer_token(self):
        session = make_session()
        assert session.session_id == "bearer-token-123"

    def test_successful_login_stores_home_id(self):
        session = make_session()
        assert session.home_id == "12345"

    def test_failed_login_raises_login_invalid_error(self):
        with patch("kryten.smart_home.sessions.tado.Thread"), \
             patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response({}, status_code=401)
            with pytest.raises(LoginInvalidError):
                TadoSession("bad@user.com", "wrongpassword")


class TestTadoSessionApiCall:
    def test_get_request_sends_bearer_token(self):
        session = make_session()
        with patch("requests.get") as mock_get:
            mock_get.return_value = make_mock_response({"some": "data"})
            session.execute_api_call("v2/someendpoint")
            headers = mock_get.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer bearer-token-123"

    def test_401_response_triggers_session_recreation_and_retry(self):
        with patch("kryten.smart_home.sessions.tado.Thread"), \
             patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:
            mock_post.return_value = make_mock_response(OAUTH_SUCCESS)
            mock_get.side_effect = [
                make_mock_response(HOME_DETAILS),           # initial /v1/me
                make_mock_response({}, status_code=401),    # first call → 401
                make_mock_response(HOME_DETAILS),           # /v1/me during re-auth
                make_mock_response({"ok": True}),           # retry → 200
            ]
            session = TadoSession("user@example.com", "password123")
            result = session.execute_api_call("v2/zones")

        assert result == {"ok": True}

    def test_connection_error_returns_empty_dict(self):
        session = make_session()
        with patch("requests.get") as mock_get:
            mock_get.side_effect = req.ConnectionError("Connection refused")
            result = session.execute_api_call("v2/someendpoint")
        assert result == {}

    def test_json_decode_error_returns_empty_dict(self):
        session = make_session()
        with patch("requests.get") as mock_get:
            bad_response = MagicMock()
            bad_response.status_code = 200
            bad_response.json.side_effect = JSONDecodeError("error", "", 0)
            mock_get.return_value = bad_response
            result = session.execute_api_call("v2/someendpoint")
        assert result == {}

    def test_empty_response_returns_empty_dict(self):
        session = make_session()
        with patch("requests.get") as mock_get:
            mock_get.return_value = make_mock_response({})
            result = session.execute_api_call("v2/someendpoint")
        assert result == {}
