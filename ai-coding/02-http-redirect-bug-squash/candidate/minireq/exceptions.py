"""Exceptions raised by minireq. All of them derive from RequestException."""
import json


class RequestException(IOError):
    """Something went wrong while handling a request."""

    def __init__(self, *args, response=None, request=None):
        self.response = response
        self.request = request
        if response is not None and request is None and hasattr(response, "request"):
            self.request = response.request
        super().__init__(*args)


class InvalidJSONError(RequestException):
    """A JSON body could not be encoded."""


class JSONDecodeError(InvalidJSONError, json.JSONDecodeError):
    """A response body could not be decoded as JSON."""

    def __init__(self, *args, **kwargs):
        json.JSONDecodeError.__init__(self, *args)
        InvalidJSONError.__init__(self, *self.args, **kwargs)


class HTTPError(RequestException):
    """The server answered with a 4xx or 5xx status."""


class ConnectionError(RequestException):
    """The connection failed or was dropped."""


class Timeout(RequestException):
    """The request timed out. Catch this to catch both timeout kinds."""


class ConnectTimeout(ConnectionError, Timeout):
    """Connecting to the server took longer than the connect timeout."""


class ReadTimeout(Timeout):
    """The server did not answer within the read timeout."""


class TooManyRedirects(RequestException):
    """More redirects than Session.max_redirects."""


class MissingSchema(RequestException, ValueError):
    """The URL has no scheme, e.g. "example.com/path"."""


class InvalidSchema(RequestException, ValueError):
    """No adapter is mounted for the URL's scheme."""


class InvalidURL(RequestException, ValueError):
    """The URL is not valid."""


class InvalidHeader(RequestException, ValueError):
    """A header name or value is not valid."""
