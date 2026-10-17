"""Fan events out to subscribed endpoints and deliver them, retrying failures.

    d = Dispatcher(transport, clock)
    d.endpoints.add(Endpoint("we_1", "acct_1", "https://merchant.example/hooks", "whsec_..."))
    d.publish("acct_1", "charge.succeeded", {"id": "ch_1", "amount": 500})
    d.run_due()          # send everything that is due now
"""
from hooks import serializer, signing
from hooks.clock import SystemClock
from hooks.ids import IdGenerator
from hooks.log import Logger
from hooks.models import Attempt, Delivery, Event
from hooks.retry import RetryPolicy
from hooks.store import AttemptLog, EndpointRegistry, EventStore
from hooks.transport import TIMEOUT_SECONDS, TransportTimeout

USER_AGENT = "hooks/1.4"


class Dispatcher:
    def __init__(self, transport, clock=None, policy=None, log=None, ids=None):
        self.transport = transport
        self.clock = clock or SystemClock()
        self.policy = policy or RetryPolicy()
        self.log = log or Logger(self.clock)
        self.ids = ids or IdGenerator()
        self.events = EventStore()
        self.endpoints = EndpointRegistry()
        self.attempts = AttemptLog()
        self.deliveries = []  # every Delivery ever created, oldest first

    # -- publishing ---------------------------------------------------------

    def publish(self, account_id, type, data):
        """Record an event and queue one delivery per subscribed endpoint."""
        event = Event(self.ids.new("evt"), type, account_id, self.clock.now(), data)
        self.events.add(event)
        self.log.info("event.created", event=event.id, type=type, account=account_id)
        for endpoint in self.endpoints.subscribed(event):
            self.deliveries.append(Delivery(event.id, endpoint.id, event.created, event.created))
        return event

    # -- scheduling ---------------------------------------------------------

    def pending(self):
        return [d for d in self.deliveries if d.status == "pending"]

    def next_due(self):
        """Earliest time a pending delivery is due, or None."""
        due = [d.next_attempt_at for d in self.pending()]
        return min(due) if due else None

    def run_due(self):
        """Attempt every pending delivery that is due now. Returns how many were attempted."""
        now = self.clock.now()
        due = [d for d in self.pending() if d.next_attempt_at <= now]
        due.sort(key=lambda d: (d.next_attempt_at, d.event_id, d.endpoint_id))
        for delivery in due:
            self._attempt(delivery)
        return len(due)

    def run_until(self, deadline):
        """Move a FakeClock through every attempt due up to `deadline`. Tests and replays only."""
        attempted = 0
        while (t := self.next_due()) is not None and t <= deadline:
            self.clock.set(max(t, self.clock.now()))
            attempted += self.run_due()
        self.clock.set(max(deadline, self.clock.now()))
        return attempted

    # -- delivery -----------------------------------------------------------

    def _attempt(self, d):
        event = self.events.get(d.event_id)
        endpoint = self.endpoints.get(d.endpoint_id)
        if not endpoint.enabled:
            d.status = "skipped"
            self.log.info("delivery.skipped", event=event.id, endpoint=endpoint.id, reason="endpoint_disabled")
            return

        d.attempts += 1
        delivery_id = self.ids.new("whd")
        envelope = serializer.envelope(event, delivery_id, d.attempts)
        body = serializer.to_bytes(envelope)
        now = self.clock.now()
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
            signing.HEADER: signing.sign_envelope(envelope, endpoint.secret, now),
        }
        fields = dict(event=event.id, delivery=delivery_id, endpoint=endpoint.id,
                      account=event.account_id, type=event.type, attempt=d.attempts)

        try:
            resp = self.transport.post(endpoint.url, body, headers, timeout=TIMEOUT_SECONDS)
        except TransportTimeout:
            self.attempts.add(Attempt(delivery_id, event.id, endpoint.id, d.attempts, now, "timeout"))
            self.log.warn("delivery.timeout", **fields, timeout_ms=TIMEOUT_SECONDS * 1000)
            self._retry_later(d)
            return

        if 200 <= resp.status < 300:
            self.attempts.add(Attempt(delivery_id, event.id, endpoint.id, d.attempts, now, "ok", resp.status))
            d.status = "delivered"
            self.log.info("delivery.sent", **fields, http=resp.status, bytes=len(body))
        else:
            self.attempts.add(Attempt(delivery_id, event.id, endpoint.id, d.attempts, now, "http_error", resp.status))
            self.log.warn("delivery.failed", **fields, http=resp.status, resp=resp.body[:80])
            self._retry_later(d)

    def _retry_later(self, d):
        now = self.clock.now()
        account = self.events.get(d.event_id).account_id
        at = self.policy.next_attempt_at(d.created_at, d.attempts, now)
        if at is None:
            d.status = "abandoned"
            self.log.error("delivery.gave_up", event=d.event_id, endpoint=d.endpoint_id, account=account,
                           attempts=d.attempts, age_s=now - d.created_at)
            return
        d.next_attempt_at = at
        self.log.info("delivery.retry_scheduled", event=d.event_id, endpoint=d.endpoint_id, account=account,
                      next_attempt=d.attempts + 1, in_s=at - now)
