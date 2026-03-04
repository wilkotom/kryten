# Test Coverage Analysis

## Summary

The kryten codebase currently has **zero formal test coverage**. The only file resembling a test is `test.py` in the project root, which is an informal manual example/smoke-test script rather than an automated test suite. There is no pytest configuration, no test directory, and no CI/CD pipeline.

This document identifies the highest-priority areas for introducing tests, ordered roughly by value and feasibility.

---

## Priority 1 — Pure Logic (No Mocking Required)

These are the easiest wins: self-contained logic with no external dependencies.

### `kryten/exceptions.py`

All six custom exceptions have parameterised `__init__` methods that format error messages. Simple unit tests should verify the message formatting for each.

**What to test:**
- `LoginInvalidError` formats provider and identifier into the message correctly.
- `APIOperationNotImplementedError` includes the HTTP verb and URL.
- `ImpossibleRequestError` includes the operation name and value.
- `UnexpectedResultError` includes the operation and result string.
- `DeviceIsOfflineError` includes the device name.

### `kryten/datasources/energy/static_energy_tariff.py`

`StaticEnergyTariff` is a trivial value object. It takes a `unit_rate` at construction and returns it via `current_energy_cost`. This is the simplest possible test in the entire codebase.

**What to test:**
- `current_energy_cost` returns the `unit_rate` passed to the constructor.
- Construction with and without the optional `unit_type` argument succeeds.

### `kryten/smart_home/lights/hive.py` — `HiveWarmWhiteBulb._fade()`

The `_fade` method contains meaningful pure arithmetic logic (step calculation, range iteration, interrupt handling) that can be exercised without a real Hive session, given a mock session that records `execute_api_call` calls.

**What to test:**
- Fading from a higher to lower brightness calls the API the correct number of times.
- When `end == 0`, the bulb is powered off at the end of the fade.
- When `start == end`, the method returns immediately without any API calls.
- Setting `_action_interrupt_semaphore = True` during a fade causes the fade to abort.

---

## Priority 2 — Session Layer (Mocked HTTP)

The session classes (`HiveSession`, `TadoSession`, `SolisCloudSession`) contain the most complex logic in the codebase: authentication flows, token refresh, request caching, HMAC signing, and auto-retry. These should be tested by mocking `requests` (e.g. with `unittest.mock.patch` or the `responses` library).

### `kryten/smart_home/sessions/solis_cloud.py` — `SolisCloudSession`

This is the most self-contained session and the best place to start.

**What to test:**
- HMAC-SHA1 signature is computed correctly for a known payload (deterministic, no randomness).
- `Content-MD5` header matches the base64-encoded MD5 of the request body.
- A cached response is returned without making a second HTTP request when called again within `min_refresh`.
- After `min_refresh` seconds have elapsed, a fresh HTTP request is made.
- A `ConnectionError` on the underlying request is handled gracefully (returns the last cached value).

### `kryten/smart_home/sessions/hive.py` — `HiveSession`

**What to test:**
- A successful login stores the token and calls `_refresh_hive_state`.
- An unsuccessful login (missing `token` key in response) raises `LoginInvalidError`.
- `execute_api_call` with an unsupported method raises `APIOperationNotImplementedError`.
- A `403` response triggers a session re-creation and the original call is retried.
- The `session_id` property returns the stored token.
- The `session_id` setter raises `AttributeError`.
- The `devices` property extracts the `products` list from the cached Hive state.

### `kryten/smart_home/sessions/tado.py` — `TadoSession`

**What to test:**
- A successful login stores the bearer token, refresh token, and expiry.
- A non-200 login response raises `LoginInvalidError`.
- A `401` response from `execute_api_call` triggers session re-creation and a retry.
- A `ConnectionError` from `execute_api_call` returns an empty dict `{}`.
- A `JSONDecodeError` from `execute_api_call` returns an empty dict `{}`.
- `__renew_token` uses the refresh token when the current token is near expiry.

---

## Priority 3 — Business Logic (Mocked Sessions)

Once session mocking is established, the controllers and device objects become straightforward to test.

### `kryten/smart_home/lights/hive.py` — `HiveSmartLightController`

**What to test:**
- `brightness()` with a value outside `(0, 100]` raises `ImpossibleRequestError`.
- `brightness()` for an unknown `light_id` raises `ImpossibleRequestError`.
- `_generate_light_list()` only creates `HiveWarmWhiteBulb` objects for devices with `type == "warmwhitelight"`.
- `list_lights()` returns the expected list of id/name dicts.

### `kryten/smart_home/thermostat/tado.py` — `TadoThermostatZone`

**What to test:**
- Zone state is fetched on first access.
- Zone state is NOT re-fetched within `min_refresh` seconds (caching).
- After `min_refresh` seconds a fresh API call is made.
- A `KeyError` in the API response (missing expected fields) does not raise an uncaught exception.
- `current_temperature`, `humidity`, and `target_temperature` all reflect the parsed state.

### `kryten/smart_home/thermostat/tado.py` — `TadoThermostatController` and `weather_updater`

**What to test:**
- `external_temperature` and `solar_intensity` call the weather API only when `_weather_refresh` has elapsed.
- `_get_zone_list()` filters out non-`HEATING` zone types.
- `_get_zone_list()` raises `UnexpectedResultError` when a non-list is returned by the API.
- `zones` returns the cached list on repeated calls.

---

## Priority 4 — Metrics Senders (Mocked Backends)

### `kryten/metrics/prometheus.py` — `PrometheusMetricSender`

**What to test:**
- A new metric name creates a new `Gauge` with the correct name, description, and label names.
- Calling `send_metric` twice with the same name reuses the existing `Gauge`.
- `increment=True` calls `.inc()` instead of `.set()` on the gauge.
- Tag keys and values are passed through correctly as Prometheus labels.

### `kryten/metrics/graphite.py` and `kryten/metrics/statsd.py`

**What to test (each):**
- `send_metric` invokes the underlying client with the correctly-prefixed metric name and value.
- UDP (StatsD) and TCP (StatsD) connection modes can both be initialised.
- Metric names with special characters are handled without raising exceptions.

---

## Suggested Test Infrastructure

Before writing the tests above, put the following in place:

1. **`tests/` directory** at the project root, with `__init__.py`.
2. **`pytest`** and **`pytest-mock`** (or the stdlib `unittest.mock`) as `dev` dependencies.
3. **`responses`** library for straightforward mocking of `requests` HTTP calls.
4. **`pytest.ini`** or a `[tool.pytest.ini_options]` section in `pyproject.toml` to set the test root.
5. **Fixtures** in `tests/conftest.py` for common mocked sessions (`MockHiveSession`, `MockTadoSession`, `MockSolisSession`) that return canned API responses.

A rough dependency-order for writing tests:
```
exceptions → static_energy_tariff → solis_cloud session →
hive session → tado session → hive lights → tado thermostat →
metrics senders
```

---

## Known Issues Surfaced by This Analysis

Several code paths will be exercised meaningfully for the first time by tests, and are likely to expose existing bugs:

- **`SolisCloudSession.execute_api_call`**: the `finally: return` idiom swallows exceptions — a bare `return` inside `finally` suppresses any exception that was in flight. This is almost certainly unintentional.
- **`TadoSession`**: the hardcoded `_oath_client_secret` is a public OAuth2 client secret, not a credential that needs protecting, but it is worth noting in tests that this value is expected.
- **`HiveSmartLightController._bulbs`**: declared as a class-level dict (`_bulbs: Dict[...] = {}`), meaning all instances share the same dict unless overwritten. A test creating two controllers would catch this.
- **`TadoThermostatController._zones`** and **`_zone_list`**: same class-level mutable default issue as above.
- **`HiveWarmWhiteBulb.brightness` setter**: allows setting brightness to 100 but the guard is `not 0 < val <= 100` — the boundary condition (val=100) passes, but val=0 is correctly rejected. Tests should confirm the boundary explicitly.
