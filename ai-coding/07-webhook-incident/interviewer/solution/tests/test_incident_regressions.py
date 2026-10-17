"""INC-2291 regressions. Written red first, against the public API only."""
import json
import unittest

from hooks.models import Endpoint
from hooks.retry import RetryPolicy
from hooks.transport import Response, TransportTimeout
from sdk.webhooks import verify_signature
from tests.helpers import SECRET, T0, make_dispatcher

THREE_DAYS = 3 * 24 * 3600


class SignatureCoversSentBytes(unittest.TestCase):
    def test_non_ascii_payload_verifies(self):
        d, transport, clock = make_dispatcher()
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1", "statement_descriptor": "CAFÉ OLÉ"})
        d.run_due()
        req = transport.requests[0]
        self.assertTrue(verify_signature(req.body, req.headers["Hooks-Signature"], SECRET, now=clock.now()))


class EventIdIsStableAcrossAttempts(unittest.TestCase):
    def test_retry_after_timeout_keeps_the_event_id(self):
        d, transport, _ = make_dispatcher()
        replies = iter(["timeout", "ok"])

        def slow_then_ok(body, headers):
            if next(replies) == "timeout":
                raise TransportTimeout()
            return Response(200, "ok")

        transport.route("https://merchant.example/hooks", slow_then_ok)
        event = d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_until(T0 + 3600)
        ids = [json.loads(r.body)["id"] for r in transport.requests]
        self.assertEqual(ids, [event.id, event.id])


class RetriesLastAboutThreeDays(unittest.TestCase):
    def test_policy_still_retrying_after_one_day(self):
        self.assertIsNotNone(RetryPolicy().next_attempt_at(created_at=0, attempts=8, now=86400))

    def test_dead_endpoint_is_retried_for_days(self):
        d, transport, _ = make_dispatcher()
        transport.route("https://merchant.example/hooks", lambda body, headers: Response(503, "down"))
        event = d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_until(T0 + 4 * 86400)
        last = d.attempts.for_event(event.id)[-1].at
        self.assertGreater(last - T0, 2 * 86400)
        self.assertLessEqual(last - T0, THREE_DAYS)


if __name__ == "__main__":
    unittest.main()
