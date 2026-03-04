import pytest
from unittest.mock import MagicMock, patch, call

from kryten.smart_home.lights.hive import HiveWarmWhiteBulb, HiveSmartLightController
from kryten.exceptions import ImpossibleRequestError, OperationNotImplementedError


DEVICE_DICT = {
    "id": "bulb-001",
    "type": "warmwhitelight",
    "state": {"name": "Living Room", "brightness": 50, "status": "ON"},
    "props": {"online": True},
}


def make_mock_session(devices=None, api_response=None):
    session = MagicMock()
    session.devices = devices if devices is not None else [DEVICE_DICT]
    session.execute_api_call.return_value = (
        api_response if api_response is not None else None
    )
    return session


def make_bulb(session=None, uuid="bulb-001", desc="Living Room", presence=True):
    if session is None:
        session = make_mock_session()
    return HiveWarmWhiteBulb(session, uuid, desc, presence)


class TestHiveWarmWhiteBulb:
    def test_brightness_property_returns_initial_value(self):
        bulb = make_bulb()
        assert bulb.brightness == 50

    def test_uuid_and_name(self):
        bulb = make_bulb(uuid="bulb-001", desc="Hallway")
        assert bulb.uuid == "bulb-001"
        assert bulb.name == "Hallway"

    def test_power_on_from_device_state(self):
        bulb = make_bulb()
        assert bulb.power is True

    def test_power_off_from_device_state(self):
        device = dict(DEVICE_DICT)
        device["state"] = {**DEVICE_DICT["state"], "status": "OFF"}
        session = make_mock_session(devices=[device])
        bulb = make_bulb(session=session)
        assert bulb.power is False

    def test_brightness_setter_calls_api(self):
        session = make_mock_session()
        bulb = make_bulb(session=session)
        bulb.brightness = 75
        session.execute_api_call.assert_called_with(
            path="/nodes/warmwhitelight/bulb-001",
            method="POST",
            payload={"brightness": 75},
        )
        assert bulb.brightness == 75

    def test_brightness_setter_rejects_zero(self):
        bulb = make_bulb()
        with pytest.raises(ImpossibleRequestError):
            bulb.brightness = 0

    def test_brightness_setter_rejects_negative(self):
        bulb = make_bulb()
        with pytest.raises(ImpossibleRequestError):
            bulb.brightness = -1

    def test_brightness_setter_rejects_above_100(self):
        bulb = make_bulb()
        with pytest.raises(ImpossibleRequestError):
            bulb.brightness = 101

    def test_brightness_setter_accepts_100(self):
        session = make_mock_session()
        bulb = make_bulb(session=session)
        bulb.brightness = 100
        assert bulb.brightness == 100

    def test_power_setter_sends_on(self):
        session = make_mock_session()
        bulb = make_bulb(session=session)
        bulb.power = True
        session.execute_api_call.assert_called_with(
            path="/nodes/warmwhitelight/bulb-001",
            method="POST",
            payload={"status": "ON"},
        )

    def test_power_setter_sends_off(self):
        session = make_mock_session()
        bulb = make_bulb(session=session)
        bulb.power = False
        session.execute_api_call.assert_called_with(
            path="/nodes/warmwhitelight/bulb-001",
            method="POST",
            payload={"status": "OFF"},
        )

    def test_update_attributes_from_hive(self):
        bulb = make_bulb()
        bulb._update_attributes_from_hive(brightness=30, powered=False, presence=False)
        assert bulb.brightness == 30
        assert bulb.power is False
        assert bulb._presence is False


class TestHiveWarmWhiteBulbFade:
    """Tests for _fade() — called directly, avoiding threading."""

    def _make_bulb_with_brightness(self, brightness):
        session = make_mock_session()
        bulb = make_bulb(session=session)
        bulb._brightness = brightness
        session.execute_api_call.reset_mock()
        return bulb, session

    def test_fade_down_calls_brightness_setter_for_each_step(self):
        bulb, session = self._make_bulb_with_brightness(10)
        with patch("kryten.smart_home.lights.hive.sleep"):
            bulb._fade(start=10, end=5, period=0)
        # range(10, 4, -1) → [10, 9, 8, 7, 6, 5] = 6 steps
        assert session.execute_api_call.call_count == 6

    def test_fade_start_equals_end_makes_no_api_calls(self):
        bulb, session = self._make_bulb_with_brightness(50)
        bulb._fade(start=50, end=50, period=0)
        session.execute_api_call.assert_not_called()

    def test_fade_to_zero_powers_off_at_end(self):
        bulb, session = self._make_bulb_with_brightness(5)
        with patch("kryten.smart_home.lights.hive.sleep"):
            bulb._fade(start=5, end=0, period=0)
        # 5 brightness calls (5→1) + 1 power-off call
        session.execute_api_call.assert_any_call(
            path="/nodes/warmwhitelight/bulb-001",
            method="POST",
            payload={"status": "OFF"},
        )

    def test_fade_interrupted_by_semaphore_makes_no_brightness_calls(self):
        bulb, session = self._make_bulb_with_brightness(10)
        bulb._action_interrupt_semaphore = True
        with patch("kryten.smart_home.lights.hive.sleep"):
            bulb._fade(start=10, end=5, period=0)
        # Semaphore was True on entry → loop returns immediately
        session.execute_api_call.assert_not_called()
        assert bulb._action_interrupt_semaphore is False

    def test_fade_resets_semaphore_after_interrupt(self):
        bulb, _ = self._make_bulb_with_brightness(10)
        bulb._action_interrupt_semaphore = True
        bulb._fade(start=10, end=5, period=0)
        assert bulb._action_interrupt_semaphore is False


class TestHiveSmartLightController:
    def _make_controller(self, devices=None):
        if devices is None:
            devices = [DEVICE_DICT]
        session = make_mock_session(devices=devices, api_response=devices)
        with patch("kryten.smart_home.lights.hive.Thread") as mock_thread_cls:
            mock_thread_cls.return_value = MagicMock(is_alive=MagicMock(return_value=False))
            controller = HiveSmartLightController(session)
        return controller, session

    def test_list_lights_includes_warm_white_bulbs(self):
        controller, _ = self._make_controller()
        lights = controller.list_lights()
        assert len(lights) == 1
        assert lights[0]["id"] == "bulb-001"
        assert lights[0]["name"] == "Living Room"

    def test_non_warmwhitelight_devices_are_excluded(self):
        plug_device = {
            "id": "plug-001",
            "type": "activeplug",
            "state": {"name": "Kettle", "status": "ON"},
            "props": {"online": True},
        }
        controller, _ = self._make_controller(devices=[plug_device])
        assert controller.list_lights() == []

    def test_brightness_with_zero_raises_impossible_request(self):
        controller, _ = self._make_controller()
        with pytest.raises(ImpossibleRequestError):
            controller.brightness("bulb-001", 0)

    def test_brightness_above_100_raises_impossible_request(self):
        controller, _ = self._make_controller()
        with pytest.raises(ImpossibleRequestError):
            controller.brightness("bulb-001", 101)

    def test_brightness_for_unknown_bulb_raises_impossible_request(self):
        controller, _ = self._make_controller()
        with pytest.raises(ImpossibleRequestError):
            controller.brightness("unknown-bulb-id", 50)

    def test_brightness_valid_value_calls_api(self):
        controller, session = self._make_controller()
        controller.brightness("bulb-001", 80)
        session.execute_api_call.assert_called_with(
            path="/nodes/warmwhitelight/bulb-001",
            method="POST",
            payload={"brightness": 80},
        )
