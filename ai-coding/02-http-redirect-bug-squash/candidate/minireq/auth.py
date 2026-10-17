"""Authentication handlers. An auth object is a callable that adds headers to a PreparedRequest."""
from base64 import b64encode


def _basic_auth_str(username, password):
    if isinstance(username, str):
        username = username.encode("latin1")
    if isinstance(password, str):
        password = password.encode("latin1")
    token = b64encode(b":".join((username, password))).strip().decode("ascii")
    return f"Basic {token}"


class AuthBase:
    """Base class that all auth implementations derive from."""

    def __call__(self, r):
        raise NotImplementedError("Auth hooks must be callable.")


class HTTPBasicAuth(AuthBase):
    """HTTP Basic auth. A (user, password) tuple passed as `auth=` becomes one of these."""

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __eq__(self, other):
        return (self.username, self.password) == (
            getattr(other, "username", None),
            getattr(other, "password", None),
        )

    def __call__(self, r):
        r.headers["Authorization"] = _basic_auth_str(self.username, self.password)
        return r


class HTTPBearerAuth(AuthBase):
    """`Authorization: Bearer <token>`, used for our service-to-service tokens."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r
