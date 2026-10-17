import unittest

from invoicing.errors import ProcessorError
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

    def test_decline(self):
        self.fake.decline_numbers.add(CARD.number)
        with self.assertRaises(ProcessorError):
            self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(self.fake.charges, [])

    def test_retries_timeout(self):
        self.fake.timeouts = ["before"]
        result = self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(result.amount, 2099)
        self.assertEqual(len(self.fake.charges), 1)

    def test_gives_up_after_three_attempts(self):
        self.fake.timeouts = ["before"] * 3
        with self.assertRaises(ProcessorError):
            self.client.charge(2099, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.requests), 3)


if __name__ == "__main__":
    unittest.main()
