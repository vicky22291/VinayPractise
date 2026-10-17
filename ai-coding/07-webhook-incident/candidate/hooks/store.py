"""In-memory stores. Production keeps these in Postgres behind the same methods."""


class EventStore:
    def __init__(self):
        self._events = {}

    def add(self, event):
        self._events[event.id] = event

    def get(self, event_id):
        return self._events[event_id]

    def for_account(self, account_id):
        """Events of one account, oldest first."""
        found = [e for e in self._events.values() if e.account_id == account_id]
        return sorted(found, key=lambda e: (e.created, e.id))


class EndpointRegistry:
    def __init__(self):
        self._endpoints = {}

    def add(self, endpoint):
        self._endpoints[endpoint.id] = endpoint

    def get(self, endpoint_id):
        return self._endpoints[endpoint_id]

    def all(self):
        return list(self._endpoints.values())

    def subscribed(self, event):
        """Enabled endpoints of the event's account that want this event type."""
        return [
            ep for ep in self._endpoints.values()
            if ep.enabled and ep.account_id == event.account_id and ep.wants(event.type)
        ]


class AttemptLog:
    def __init__(self):
        self._attempts = []

    def add(self, attempt):
        self._attempts.append(attempt)

    def all(self):
        return list(self._attempts)

    def for_event(self, event_id):
        return [a for a in self._attempts if a.event_id == event_id]

    def for_endpoint(self, endpoint_id):
        return [a for a in self._attempts if a.endpoint_id == endpoint_id]
