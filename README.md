# Kryten

Kryten is your friendly home assistant. It can control your lights, appliances and thermostat, and record time series data related to these.

Example code:

```python
import kryten.metrics
import kryten.smart_home.sessions
import kryten.smart_home.thermostat
import kryten.smart_home.lights.hive
from time import sleep
t = kryten.smart_home.sessions.TadoSession('Tado username', 'tado password')
s = kryten.metrics.StatsDMetricSender('statsd server')
h = kryten.smart_home.sessions.hive.HiveSession('hive username','Hive password')
tz = kryten.smart_home.thermostat.TadoThermostatController(t, s)
ls = kryten.smart_home.lights.hive.HiveSmartLightController(h, s)
ls.bulb('f5e95939-c684-488a-b2bd-a1b4c1cbed91').brightness =  50  # Set brightness of bulb to 50%
ls.bulb('f5e95939-c684-488a-b2bd-a1b4c1cbed91').sunrise()  # Gradually fade bulb up from 0 to 100%
ls.bulb('f5e95939-c684-488a-b2bd-a1b4c1cbed91').sunset()  # Gradually fade bulb down from current brightness to 0%
while True:
    sleep(86400) # Keep example program running 
```