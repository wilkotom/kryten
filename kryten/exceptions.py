class OperationNotImplementedError(Exception):
    """Kryten doesn't yet know how to do this"""


class LoginInvalidError(Exception):
    """Invalid credentials were supplied when logging in"""
    def __init__(self, provider: str="Unknown", identifier: str = "Unknown"):
        super().__init__(f"Could not log in to {provider} using credential {identifier}")


class APIOperationNotImplementedError(Exception):
    """An unsupported HTTP verb was supplied"""
    def __init__(self, operation: str = "UNKNOWN", url: str = "Unknown"):
        super().__init__(f"Can't send a {operation} request to {url}")


class ImpossibleRequestError(Exception):
    """Kryten was asked to do the impossible"""
    def __init__(self, operation: str = "Unknown", val: str = "Unknown"):
        super().__init__(f"Can't set the {operation} to {val}")


class UnexpectedResultError(Exception):
    """Kryten got something unexpected back from a remote API"""
    def __init__(self, operation: str = "Unknown", result: str = "Unknown"):
        super().__init__(f"Got an unexpected result from {operation} - result was {result}")

class DeviceIsOfflineError(Exception):
    """Attempt to access a device which is not physically powered"""
    def __init__(self, device_name: str):
        super().__init__(f"Can't interact with the offline device: {device_name}")

