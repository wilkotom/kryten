class KrytenOperationNotImplemented(Exception):
    """Kryten doesn't yet know how to do this"""


class LoginInvalid(Exception):
    """Invalid credentials were supplied when logging in"""
    def __init__(self, provider: str="Unknown", identifier: str = "Unknown"):
        super().__init__(f"Could not log in to {provider} using credential {identifier}")
