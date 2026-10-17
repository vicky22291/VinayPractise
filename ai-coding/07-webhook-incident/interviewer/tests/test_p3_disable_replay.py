import json
import unittest

from hooks.clock import FakeClock
from hooks.dispatcher import Dispatcher
from hooks.models import Endpoint
from hooks.transport import FakeTransport, Response

T0 = 1_791_968_400
DAY = 86400
URL = "https://m.example/hooks"


class Recorder:
    def __init__(self):
        self.sent = []

    def endpoint_disabled(self, endpoint_id, account_id, at):
        self.sent.append((endpoint_id, account_id, at))


def make(up=lambda now: False, types=("*",)):
    clock = FakeClock(T0)
    transport = FakeTransport()
    rec = Recorder()
    d = Dispatcher(transport, clock, notifier=rec)
    d.endpoints.add(Endpoint("we_1", "acct_1", URL, "whsec_x", types))
    transport.route(URL, lambda body, headers: Response(200 if up(clock.now()) else 503, ""))
    return d, transport, clock, rec


def hourly(d, clock, hours, type="charge.succeeded"):
    for h in range(hours):
        d.run_until(T0 + h * 3600)
        d.publish("acct_1", type, {"n": h})
        d.run_due()


class Part3(unittest.TestCase):
    def test_disabled_after_three_days_of_failures(self):
        d, t, clock, rec = make()
        hourly(d, clock, 5 * 24)
        self.assertFalse(d.endpoints.get("we_1").enabled)
        self.assertEqual(len(rec.sent), 1)
        endpoint_id, account_id, at = rec.sent[0]
        self.assertEqual((endpoint_id, account_id), ("we_1", "acct_1"))
        self.assertGreater(at - T0, 3 * DAY)
        self.assertLessEqual(at - T0, 3 * DAY + 2 * 3600)

    def test_nothing_sent_after_disable(self):
        d, t, clock, rec = make()
        hourly(d, clock, 5 * 24)
        at = rec.sent[0][2]
        before = len(t.requests)
        d.run_until(T0 + 8 * DAY)
        self.assertEqual(len(t.requests), before)
        self.assertEqual(d.pending(), [])
        self.assertTrue(all(x.status in ("skipped", "abandoned") for x in d.deliveries))
        self.assertIn("skipped", {x.status for x in d.deliveries})
        self.assertGreater(at, T0)

    def test_success_resets_the_streak(self):
        # Down for two days, up for one hour, down again for two days.
        up = lambda now: 2 * DAY <= now - T0 < 2 * DAY + 3600
        d, t, clock, rec = make(up)
        hourly(d, clock, 4 * 24)
        self.assertTrue(d.endpoints.get("we_1").enabled)
        self.assertEqual(rec.sent, [])

    def test_not_disabled_before_three_days(self):
        d, t, clock, rec = make()
        hourly(d, clock, 3 * 24 - 2)
        self.assertTrue(d.endpoints.get("we_1").enabled)

    def test_enable_then_replay_with_original_ids(self):
        d, t, clock, rec = make(up=lambda now: now - T0 >= 6 * DAY)
        hourly(d, clock, 5 * 24)
        self.assertFalse(d.endpoints.get("we_1").enabled)
        clock.set(T0 + 6 * DAY)
        with self.assertRaises(ValueError):
            d.replay("we_1", since=T0)
        d.enable("we_1")
        queued = d.replay("we_1", since=T0 + 4 * DAY)
        self.assertEqual(queued, 24)
        n = len(t.requests)
        d.run_due()
        replayed = [json.loads(r.body) for r in t.requests[n:]]
        self.assertEqual(len(replayed), 24)
        created = {e.id for e in d.events.for_account("acct_1") if e.created >= T0 + 4 * DAY}
        self.assertEqual({r["id"] for r in replayed}, created)

    def test_replay_respects_subscription_and_since(self):
        d, t, clock, rec = make(up=lambda now: True, types=("payout.paid",))
        d.publish("acct_1", "payout.paid", {"n": 1})
        clock.advance(10)
        d.publish("acct_1", "charge.succeeded", {"n": 2})
        clock.advance(10)
        d.publish("acct_1", "payout.paid", {"n": 3})
        d.run_due()
        self.assertEqual(d.replay("we_1", since=T0 + 1), 1)
        self.assertEqual(d.replay("we_1", since=T0), 2)

    def test_old_replayed_event_gets_a_fresh_retry_window(self):
        # Delivered once. Replayed 10 days later: the first replay attempt fails, the retry works.
        state = {"calls": 0}

        def flaky(now):
            state["calls"] += 1
            return state["calls"] != 2

        d, t, clock, rec = make(up=flaky)
        event = d.publish("acct_1", "payout.paid", {"n": 1})
        d.run_due()
        clock.set(T0 + 10 * DAY)
        d.replay("we_1", since=T0)
        d.run_until(T0 + 10 * DAY + 3600)
        self.assertEqual(d.deliveries[-1].status, "delivered")
        self.assertEqual(json.loads(t.requests[-1].body)["id"], event.id)


if __name__ == "__main__":
    unittest.main()
