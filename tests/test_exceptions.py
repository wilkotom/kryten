import pytest

from kryten.exceptions import (
    OperationNotImplementedError,
    LoginInvalidError,
    APIOperationNotImplementedError,
    ImpossibleRequestError,
    UnexpectedResultError,
    DeviceIsOfflineError,
)


class TestLoginInvalidError:
    def test_message_contains_provider_and_identifier(self):
        err = LoginInvalidError("Hive", "user@example.com")
        assert "Hive" in str(err)
        assert "user@example.com" in str(err)

    def test_defaults(self):
        err = LoginInvalidError()
        assert "Unknown" in str(err)

    def test_is_exception(self):
        with pytest.raises(LoginInvalidError):
            raise LoginInvalidError("Tado", "myuser")


class TestAPIOperationNotImplementedError:
    def test_message_contains_verb_and_url(self):
        err = APIOperationNotImplementedError("DELETE", "https://api.example.com/resource")
        assert "DELETE" in str(err)
        assert "https://api.example.com/resource" in str(err)

    def test_defaults(self):
        err = APIOperationNotImplementedError()
        assert "UNKNOWN" in str(err)
        assert "Unknown" in str(err)

    def test_is_exception(self):
        with pytest.raises(APIOperationNotImplementedError):
            raise APIOperationNotImplementedError("PATCH", "/some/path")


class TestImpossibleRequestError:
    def test_message_contains_operation_and_value(self):
        err = ImpossibleRequestError("Bulb Brightness", "150")
        assert "Bulb Brightness" in str(err)
        assert "150" in str(err)

    def test_defaults(self):
        err = ImpossibleRequestError()
        assert "Unknown" in str(err)

    def test_is_exception(self):
        with pytest.raises(ImpossibleRequestError):
            raise ImpossibleRequestError("brightness", "0")


class TestUnexpectedResultError:
    def test_message_contains_operation_and_result(self):
        err = UnexpectedResultError("zone list", "[1, 2, 3]")
        assert "zone list" in str(err)
        assert "[1, 2, 3]" in str(err)

    def test_defaults(self):
        err = UnexpectedResultError()
        assert "Unknown" in str(err)

    def test_is_exception(self):
        with pytest.raises(UnexpectedResultError):
            raise UnexpectedResultError("login", "None")


class TestDeviceIsOfflineError:
    def test_message_contains_device_name(self):
        err = DeviceIsOfflineError("Living Room Light")
        assert "Living Room Light" in str(err)

    def test_is_exception(self):
        with pytest.raises(DeviceIsOfflineError):
            raise DeviceIsOfflineError("Lamp")


class TestOperationNotImplementedError:
    def test_is_exception(self):
        with pytest.raises(OperationNotImplementedError):
            raise OperationNotImplementedError()
