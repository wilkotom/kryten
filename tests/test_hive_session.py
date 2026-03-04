import pytest
from unittest.mock import patch, MagicMock

from kryten.smart_home.sessions.hive import HiveSession
from kryten.exceptions import (
    LoginInvalidError,
    APIOperationNotImplementedError,
    UnexpectedResultError,
)

_ORIGINAL_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Kryten 2X4B 523P",
}

LOGIN_SUCCESS = {"token": "test-token-abc123"}
ADMIN_LOGIN_SUCCESS = {
    "products": [
        {
            "id": "bulb-001",
            "type": "warmwhitelight",
            "state": {"name": "Hallway", "status": "ON", "brightness": 50},
            "props": {"online": True},
        }
    ]
}


def make_mock_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    return mock


def reset_class_state():
    """Reset HiveSession class-level mutable state between tests."""
    HiveSession._request_headers = dict(_ORIGINAL_REQUEST_HEADERS)
    HiveSession._session = None
    HiveSession._stopping = False


def make_session(post_responses=None, get_responses=None):
    """Create a HiveSession with fully mocked HTTP and no background threads."""
    reset_class_state()
    if post_responses is None:
        post_responses = [
            make_mock_response(LOGIN_SUCCESS),
            make_mock_response(ADMIN_LOGIN_SUCCESS),
        ]
    with patch("kryten.smart_home.sessions.hive.Thread"), \
         patch("requests.post") as mock_post, \
         patch("requests.get") as mock_get:
        mock_post.side_effect = post_responses
        if get_responses:
            mock_get.side_effect = get_responses
        session = HiveSession("user@example.com", "password123")
    return session


class TestHiveSessionLogin:
    def setup_method(self):
        reset_class_state()

    def test_successful_login_stores_token(self):
        session = make_session()
        assert session.session_id == "test-token-abc123"

    def test_failed_login_raises_login_invalid_error(self):
        reset_class_state()
        with patch("kryten.smart_home.sessions.hive.Thread"), \
             patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response({"error": "bad credentials"})
            with pytest.raises(LoginInvalidError):
                HiveSession("bad@user.com", "wrongpassword")

    def test_non_dict_login_response_raises_unexpected_result(self):
        reset_class_state()
        with patch("kryten.smart_home.sessions.hive.Thread"), \
             patch("requests.post") as mock_post:
            mock_post.return_value = make_mock_response([1, 2, 3])
            with pytest.raises(UnexpectedResultError):
                HiveSession("user@example.com", "password")


class TestHiveSessionProperties:
    def setup_method(self):
        reset_class_state()

    def test_session_id_setter_raises_attribute_error(self):
        session = make_session()
        with pytest.raises(AttributeError):
            session.session_id = "forced-session"

    def test_devices_returns_products_list(self):
        session = make_session()
        devices = session.devices
        assert isinstance(devices, list)
        assert devices[0]["id"] == "bulb-001"

    def test_devices_setter_raises_attribute_error(self):
        session = make_session()
        with pytest.raises(AttributeError):
            session.devices = []


class TestHiveSessionApiCall:
    def setup_method(self):
        reset_class_state()

    def test_unsupported_method_raises_api_operation_error(self):
        session = make_session()
        with pytest.raises(APIOperationNotImplementedError):
            session.execute_api_call(path="/some/path", method="DELETE")

    def test_403_triggers_session_recreation_and_retry(self):
        reset_class_state()
        with patch("kryten.smart_home.sessions.hive.Thread"), \
             patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:
            mock_post.side_effect = [
                make_mock_response(LOGIN_SUCCESS),       # initial login
                make_mock_response(ADMIN_LOGIN_SUCCESS), # initial state refresh
                make_mock_response(LOGIN_SUCCESS),       # re-auth login
                make_mock_response(ADMIN_LOGIN_SUCCESS), # re-auth state refresh
            ]
            mock_get.side_effect = [
                make_mock_response({}, status_code=403), # first attempt → 403
                make_mock_response({"result": "ok"}),    # retry → 200
            ]
            session = HiveSession("user@example.com", "password123")
            result = session.execute_api_call(path="/some/path", method="GET")

        assert result == {"result": "ok"}

    def test_get_request_is_executed(self):
        reset_class_state()
        with patch("kryten.smart_home.sessions.hive.Thread"), \
             patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:
            mock_post.side_effect = [
                make_mock_response(LOGIN_SUCCESS),
                make_mock_response(ADMIN_LOGIN_SUCCESS),
            ]
            mock_get.return_value = make_mock_response({"data": "value"})
            session = HiveSession("user@example.com", "password123")
            result = session.execute_api_call(path="/devices", method="GET")

        assert result == {"data": "value"}
