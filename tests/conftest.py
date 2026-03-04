"""
conftest.py – global pytest configuration.

graphyte cannot be built on this system (build toolchain issue), so we inject
a lightweight stub into sys.modules before any test module is imported.  All
tests that exercise graphyte go on to patch the stub's symbols as normal.
"""
import sys
from unittest.mock import MagicMock

# Stub graphyte before any kryten.metrics module is imported
if "graphyte" not in sys.modules:
    stub = MagicMock()
    sys.modules["graphyte"] = stub
