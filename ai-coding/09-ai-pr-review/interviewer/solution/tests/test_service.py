import unittest

from invoicing.errors import ProcessorError
from invoicing.models import Card, Invoice, LineItem
from invoicing.processor import ProcessorClient
from invoicing.service import bill
from invoicing.transport import FakeProcessor

CARD = Card("4000000000000002", 1, 2031)


class BillTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeProcessor()
        self.client = ProcessorClient(self.fake)

    def test_paid(self):
        inv = Invoice("in_1", "cus_1", [LineItem("Plan", 1000)])
        self.assertEqual(bill(inv, CARD, self.client), "paid")
        self.assertEqual(inv.charge_id, "ch_1")

    def test_paid_in_jpy(self):
        inv = Invoice("in_5", "cus_1", [LineItem("Plan", 3000)], currency="jpy")
        self.assertEqual(bill(inv, CARD, self.client), "paid")
        self.assertEqual((self.fake.charges[0]["amount"], self.fake.charges[0]["currency"]), (3000, "jpy"))

    def test_declined_marks_failed(self):
        self.fake.decline_numbers.add(CARD.number)
        inv = Invoice("in_2", "cus_1", [LineItem("Plan", 1000)])
        self.assertEqual(bill(inv, CARD, self.client), "failed")

    def test_free_invoice_is_paid_without_a_charge(self):
        inv = Invoice("in_3", "cus_1", [LineItem("Coupon plan", 0)])
        self.assertEqual(bill(inv, CARD, self.client), "paid")
        self.assertEqual(self.fake.charges, [])

    def test_bad_line_is_not_marked_paid(self):
        inv = Invoice("in_6", "cus_1", [LineItem("Plan", 1000, 1, "abc")])
        with self.assertRaises(ValueError):
            bill(inv, CARD, self.client)
        self.assertEqual(inv.status, "open")
        self.assertEqual(self.fake.requests, [])

    def test_processor_down_leaves_invoice_open(self):
        self.fake.timeouts = ["before"] * 3
        inv = Invoice("in_7", "cus_1", [LineItem("Plan", 1000)])
        with self.assertRaises(ProcessorError):
            bill(inv, CARD, self.client)
        self.assertEqual(inv.status, "open")

    def test_not_open(self):
        inv = Invoice("in_4", "cus_1", [LineItem("Plan", 1000)], status="paid")
        with self.assertRaises(ValueError):
            bill(inv, CARD, self.client)


if __name__ == "__main__":
    unittest.main()
