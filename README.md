# Kryten

Kryten is your friendly home assistant. It can control your lights, appliances and thermostat.

Example code:

```python
import kryten.sessions.hive
import kryten.smart_home.lights.hive

h = kryten.sessions.hive.HiveSession('Hive Username','Hive Password')
ls = kryten.smart_home.lights.hive.HiveSmartLightController(h)

ls.list_lights()  # Show available bulbs
ls.brightness('f5e95939-c684-488a-b2bd-a1b4c1cbed91', 50)  # Set brightness of bulb to 50%
```