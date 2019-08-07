import kryten.smart_home.sessions.hive
import kryten.smart_home.lights.hive
from time import sleep;
h = kryten.smart_home.sessions.HiveSession('tom.hive@dentrassi.net', 'sekrit', debug=True)
ls = kryten.smart_home.lights.HiveSmartLightController(h)
x = 1
while x > 0:
  print(x)
  ls.brightness('f5e95939-c684-488a-b2bd-a1b4c1cbed91', x)
  x -= 1
  sleep(1)
