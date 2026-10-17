"""HTTP transport. Production wraps urllib3. Tests and incident replays use FakeTransport."""
from dataclasses import dataclass

TIMEOUT_SECONDS = 30


class TransportTimeout(Exception):
    """No response within TIMEOUT_SECONDS."""


@dataclass(frozen=True)
class Response:
    status: int
    body: str = ""


@dataclass(frozen=True)
class Request:
    url: str
    body: bytes
    headers: dict


class FakeTransport:
    """Routes each POST to handler(body, headers), which returns a Response or raises TransportTimeout."""

    def __init__(self):
        self.routes = {}
        self.requests = []

    def route(self, url, handler):
        self.routes[url] = handler

    def post(self, url, body, headers, timeout=TIMEOUT_SECONDS):
        self.requests.append(Request(url, body, dict(headers)))
        handler = self.routes.get(url)
        if handler is None:
            return Response(404, "no route")
        return handler(body, headers)
