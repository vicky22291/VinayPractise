import logging
import unittest

from invoicing.errors import CardDeclined, ProcessorError
from invoicing.models import Card
from invoicing.processor import ProcessorClient
from invoicing.transport import FakeProcessor

CARD = Card("4242424242424242", 12, 2030)


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeProcessor()
        self.client = ProcessorClient(self.fake)

    def test_charge(self):
        result = self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual((result.amount, result.currency), (2099, "usd"))
        self.assertEqual(len(self.fake.charges), 1)

    def test_request_body(self):
        self.client.charge(500, "usd", CARD, "in_7")
        path, body, _ = self.fake.requests[0]
        self.assertEqual(path, "/v1/charges")
        self.assertEqual(body["metadata"], {"invoice_id": "in_7"})

    def test_decline_is_not_retried(self):
        self.fake.decline_numbers.add(CARD.number)
        with self.assertRaises(CardDeclined):
            self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.requests), 1)
        self.assertEqual(self.fake.charges, [])

    def test_retries_timeout_before_processing(self):
        self.fake.timeouts = ["before"]
        self.assertEqual(self.client.charge(2099, "usd", CARD, "in_1").amount, 2099)
        self.assertEqual(len(self.fake.charges), 1)

    def test_lost_response_does_not_charge_twice(self):
        # The processor created the charge, then the response was lost.
        self.fake.timeouts = ["after"]
        result = self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.charges), 1)
        self.assertEqual(result.id, "ch_1")

    def test_one_key_per_call(self):
        self.fake.timeouts = ["before", "after"]
        self.client.charge(2099, "usd", CARD, "in_1")
        self.client.charge(2099, "usd", CARD, "in_2")
        keys = [h["Idempotency-Key"] for _, _, h in self.fake.requests]
        self.assertEqual(len(set(keys[:3])), 1)
        self.assertNotEqual(keys[0], keys[3])

    def test_gives_up_after_three_attempts(self):
        self.fake.timeouts = ["before"] * 3
        with self.assertRaises(ProcessorError):
            self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.requests), 3)

    def test_never_logs_card_number(self):
        with self.assertLogs("invoicing", level="DEBUG") as logs:
            self.fake.timeouts = ["before"]
            self.client.charge(2099, "usd", CARD, "in_1")
        self.assertFalse([line for line in logs.output if CARD.number in line])
        self.assertTrue([line for line in logs.output if CARD.last4 in line])


if __name__ == "__main__":
    unittest.main()
