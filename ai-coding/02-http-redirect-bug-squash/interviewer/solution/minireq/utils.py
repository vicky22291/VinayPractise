"""Helpers shared by models, sessions and adapters."""
import io
import os
from collections.abc import Mapping
from urllib.parse import unquote, urlparse

from minireq.__version__ import __version__
from minireq.exceptions import InvalidHeader, UnrewindableBodyError
from minireq.structures import CaseInsensitiveDict

DEFAULT_PORTS = {"http": 80, "https": 443}


def default_user_agent(name="python-minireq"):
    return f"{name}/{__version__}"


def default_headers():
    return CaseInsensitiveDict(
        {
            "User-Agent": default_user_agent(),
            "Accept-Encoding": "identity",
            "Accept": "*/*",
        }
    )


def super_len(o):
    """How many bytes of `o` are left to send, from its current position.

    Works for bytes, str, and file-like objects. Returns 0 when the length
    cannot be known (generators, sockets), which tells the caller to fall back
    to chunked transfer encoding.
    """
    total_length = None
    current_position = 0

    if isinstance(o, str):
        o = o.encode("utf-8")

    if hasattr(o, "__len__"):
        total_length = len(o)
    elif hasattr(o, "len"):
        total_length = o.len
    elif hasattr(o, "fileno"):
        try:
            fileno = o.fileno()
        except (io.UnsupportedOperation, AttributeError):
            pass
        else:
            total_length = os.fstat(fileno).st_size

    if hasattr(o, "tell"):
        try:
            current_position = o.tell()
        except OSError:
            # The stream has no position (a pipe, a socket): treat it as fully
            # unread and let the caller stream it.
            if total_length is not None:
                current_position = total_length
        else:
            if hasattr(o, "seek") and total_length is None:
                try:
                    o.seek(0, io.SEEK_END)
                    total_length = o.tell()
                    o.seek(current_position or 0)
                except OSError:
                    total_length = 0

    if total_length is None:
        total_length = 0
    return max(0, total_length - current_position)


def to_key_val_list(value):
    """Turn a dict or an iterable of pairs into a list of (key, value) tuples."""
    if value is None:
        return None
    if isinstance(value, (str, bytes, bool, int)):
        raise ValueError("cannot encode objects that are not 2-tuples")
    if isinstance(value, Mapping):
        value = value.items()
    return list(value)


def get_encoding_from_headers(headers):
    """The charset from a Content-Type header, or a sensible default."""
    content_type = headers.get("content-type")
    if not content_type:
        return None
    ctype, _, params = content_type.partition(";")
    for param in params.split(";"):
        key, _, value = param.strip().partition("=")
        if key.lower() == "charset":
            return value.strip("'\"")
    if "text" in ctype:
        return "ISO-8859-1"
    if "application/json" in ctype:
        return "utf-8"
    return None


def get_auth_from_url(url):
    """(username, password) embedded in a URL, or ("", "")."""
    parsed = urlparse(url)
    try:
        return unquote(parsed.username), unquote(parsed.password)
    except (AttributeError, TypeError):
        return "", ""


def check_header_validity(header):
    """Reject header names or values that would let a caller inject extra headers."""
    name, value = header
    if not isinstance(name, str) or not isinstance(value, (str, bytes)):
        raise InvalidHeader(f"Header {name!r} must be str with a str or bytes value")
    text = value.decode("latin1") if isinstance(value, bytes) else value
    if any(c in name for c in "\r\n:") or any(c in text for c in "\r\n"):
        raise InvalidHeader(f"Invalid character in header {name!r}")


def rewind_body(prepared_request):
    """Put a streamed request body back where the caller left it, so a redirect can resend it.

    Seeks to the position prepare_body recorded, not to 0: the caller may have
    read part of the stream before handing it over. Raises UnrewindableBodyError
    when there is no recorded position or the seek fails.
    """
    body_seek = getattr(prepared_request.body, "seek", None)
    position = prepared_request._body_position
    if body_seek is None or not isinstance(position, int):
        raise UnrewindableBodyError("Unable to rewind request body for redirect.", request=prepared_request)
    try:
        body_seek(position)
    except OSError:
        raise UnrewindableBodyError(
            "An error occurred when rewinding request body for redirect.", request=prepared_request
        ) from None
