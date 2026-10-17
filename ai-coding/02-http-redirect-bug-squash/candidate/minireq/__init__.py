"""minireq: the HTTP client our internal services use. The API follows requests.

    >>> import minireq
    >>> r = minireq.get("http://127.0.0.1:8000/get", params={"q": "1"}, timeout=5)
    >>> r.status_code
    200
"""
from minireq.__version__ import __title__, __version__
from minireq import exceptions
from minireq.api import delete, get, head, options, patch, post, put, request
from minireq.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    ReadTimeout,
    RequestException,
    Timeout,
    TooManyRedirects,
)
from minireq.models import PreparedRequest, Request, Response
from minireq.sessions import Session, session
from minireq.status_codes import codes
