import json
import unittest

from hooks.models import Endpoint
from hooks.transport import Response
from sdk.webhooks import construct_event
from tests.helpers import SECRET, T0, make_dispatcher


class DispatcherTest(unittest.TestCase):
    def test_delivers_signed_event(self):
        d, transport, clock = make_dispatcher()
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1", "amount": 500, "currency": "usd"})
        self.assertEqual(d.run_due(), 1)
        req = transport.requests[0]
        event = construct_event(req.body, req.headers["Hooks-Signature"], SECRET, now=clock.now())
        self.assertEqual(event["type"], "charge.succeeded")
        self.assertEqual(event["data"]["object"]["amount"], 500)
        self.assertEqual(d.deliveries[0].status, "delivered")

    def test_only_subscribed_endpoints_of_the_account(self):
        d, transport, _ = make_dispatcher(
            Endpoint("we_1", "acct_1", "https://a.example/h", SECRET, ("charge.succeeded",)),
            Endpoint("we_2", "acct_1", "https://b.example/h", SECRET, ("payout.paid",)),
            Endpoint("we_3", "acct_2", "https://c.example/h", SECRET),
        )
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_due()
        self.assertEqual([r.url for r in transport.requests], ["https://a.example/h"])

    def test_retries_after_server_error(self):
        d, transport, clock = make_dispatcher()
        replies = iter([Response(500, "boom"), Response(200, "ok")])
        transport.route("https://merchant.example/hooks", lambda body, headers: next(replies))
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_due()
        self.assertEqual(d.deliveries[0].status, "pending")
        self.assertEqual(d.next_due(), T0 + 120)
        d.run_until(T0 + 3600)
        self.assertEqual(d.deliveries[0].status, "delivered")
        self.assertEqual([a.outcome for a in d.attempts.all()], ["http_error", "ok"])

    def test_disabled_endpoint_is_skipped(self):
        d, transport, _ = make_dispatcher()
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.endpoints.get("we_1").enabled = False
        d.run_due()
        self.assertEqual(transport.requests, [])
        self.assertEqual(d.deliveries[0].status, "skipped")

    def test_body_is_compact_json(self):
        d, transport, _ = make_dispatcher()
        d.publish("acct_1", "payout.paid", {"id": "po_1", "amount": 12000})
        d.run_due()
        body = transport.requests[0].body
        self.assertNotIn(b", ", body)
        self.assertEqual(json.loads(body)["account"], "acct_1")

    def test_log_lines(self):
        d, _, _ = make_dispatcher()
        d.publish("acct_1", "charge.succeeded", {"id": "ch_1"})
        d.run_due()
        self.assertTrue(d.log.sink[0].startswith("2026-10-14T09:00:00Z INFO event.created"))
        self.assertIn("delivery.sent", d.log.sink[1])


if __name__ == "__main__":
    unittest.main()
