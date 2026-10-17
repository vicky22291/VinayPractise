import json
import unittest

from hooks import signing
from hooks.clock import FakeClock
from hooks.dispatcher import Dispatcher
from hooks.models import Endpoint
from hooks.transport import FakeTransport, Response, TransportTimeout
from sdk.webhooks import construct_event, verify_signature

T0 = 1_791_968_400
SECRET = "whsec_hidden"
URL = "https://m.example/hooks"


def make(handler=None):
    clock = FakeClock(T0)
    transport = FakeTransport()
    d = Dispatcher(transport, clock)
    d.endpoints.add(Endpoint("we_1", "acct_1", URL, SECRET))
    transport.route(URL, handler or (lambda body, headers: Response(200, "ok")))
    return d, transport, clock


class Part2(unittest.TestCase):
    def test_non_ascii_payload_verifies(self):
        d, t, clock = make()
        d.publish("acct_1", "charge.succeeded", {"descriptor": "MÜLLER FAHRRÄDER", "name": "Zoë", "city": "東京"})
        d.run_due()
        req = t.requests[0]
        event = construct_event(req.body, req.headers[signing.HEADER], SECRET, now=clock.now())
        self.assertEqual(event["data"]["object"]["name"], "Zoë")

    def test_body_stays_compact_utf8(self):
        d, t, _ = make()
        d.publish("acct_1", "charge.succeeded", {"descriptor": "CAFÉ OLÉ"})
        d.run_due()
        body = t.requests[0].body
        self.assertIn("CAFÉ OLÉ".encode("utf-8"), body)
        self.assertNotIn(b"\\u00c9", body)
        self.assertNotIn(b", ", body)

    def test_body_unchanged_apart_from_id(self):
        d, t, _ = make()
        event = d.publish("acct_1", "payout.paid", {"id": "po_1", "amount": 100})
        d.run_due()
        got = json.loads(t.requests[0].body)
        self.assertEqual(got, {
            "id": event.id, "object": "event", "api_version": "2026-09-30", "type": "payout.paid",
            "account": "acct_1", "created": T0, "data": {"object": {"id": "po_1", "amount": 100}},
            "request": {"attempt": 1},
        })

    def test_ascii_signature_matches_sent_bytes(self):
        d, t, clock = make()
        d.publish("acct_1", "payout.paid", {"id": "po_1"})
        d.run_due()
        req = t.requests[0]
        self.assertEqual(req.headers[signing.HEADER], signing.sign(req.body, SECRET, clock.now()))

    def test_same_event_id_on_every_attempt(self):
        replies = iter(["timeout", 500, "timeout", 200])

        def handler(body, headers):
            r = next(replies)
            if r == "timeout":
                raise TransportTimeout()
            return Response(r, "")

        d, t, _ = make(handler)
        event = d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_until(T0 + 86400)
        self.assertEqual({json.loads(r.body)["id"] for r in t.requests}, {event.id})
        self.assertEqual(len(t.requests), 4)

    def test_retries_span_about_three_days(self):
        d, t, _ = make(lambda body, headers: Response(503, "down"))
        event = d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_until(T0 + 5 * 86400)
        attempts = d.attempts.for_event(event.id)
        ages = [a.at - T0 for a in attempts]
        self.assertGreaterEqual(ages[-1], int(2.5 * 86400))
        self.assertLessEqual(ages[-1], 3 * 86400)
        self.assertEqual(d.deliveries[0].status, "abandoned")

    def test_schedule_shape_unchanged(self):
        d, t, _ = make(lambda body, headers: Response(503, "down"))
        event = d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_until(T0 + 5 * 86400)
        times = [a.at for a in d.attempts.for_event(event.id)]
        gaps = [b - a for a, b in zip(times, times[1:])]
        self.assertEqual(gaps[:4], [120, 240, 480, 960])
        self.assertEqual(max(gaps), 6 * 3600)


if __name__ == "__main__":
    unittest.main()
