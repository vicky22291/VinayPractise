"""Records kept by the dispatcher."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    id: str
    type: str
    account_id: str
    created: int
    data: dict


@dataclass
class Endpoint:
    id: str
    account_id: str
    url: str
    secret: str
    event_types: tuple = ("*",)
    enabled: bool = True

    def wants(self, event_type):
        return "*" in self.event_types or event_type in self.event_types


@dataclass
class Delivery:
    """One event on its way to one endpoint. Lives until it is delivered or abandoned."""
    event_id: str
    endpoint_id: str
    created_at: int
    next_attempt_at: int
    attempts: int = 0
    status: str = "pending"  # pending, delivered, abandoned, skipped


@dataclass(frozen=True)
class Attempt:
    """One HTTP POST. A delivery makes one or more attempts."""
    id: str
    event_id: str
    endpoint_id: str
    number: int
    at: int
    outcome: str  # ok, http_error, timeout
    http_status: int | None = None
