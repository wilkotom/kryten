class OperationNotImplemented(Exception):
    """Kryten doesn't yet know how to do this"""


class LoginInvalid(Exception):
    """Invalid credentials were supplied when logging in"""
    def __init__(self, provider: str="Unknown", identifier: str = "Unknown"):
        super().__init__(f"Could not log in to {provider} using credential {identifier}")


class APIOperationNotImplemented(Exception):
    """An unsupported HTTP verb was supplied"""
    def __init__(self, operation: str = "UNKNOWN", url: str = "Unknown"):
        super().__init__(f"Can't send a {operation} request to {url}")


class ImpossibleRequestError(Exception):
    """Kryten was asked to do the impossible"""
    def __init__(self, operation: str = "Unknown", val: str = "Unknown"):
        super().__init__(f"Can't set the {operation} to {val}")