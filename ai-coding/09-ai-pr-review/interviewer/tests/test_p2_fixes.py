import logging
import unittest

from invoicing.currency import CachedRates, StaticRates, convert, exponent, format_amount
from invoicing.errors import CardDeclined, ProcessorError
from invoicing.models import Card, Invoice, LineItem
from invoicing.processor import ProcessorClient
from invoicing.service import bill
from invoicing.totals import invoice_total
from invoicing.transport import FakeProcessor

CARD = Card("4242424242424242", 12, 2030)


class FakeClock:
    def __init__(self):
        self.now = 1000

    def __call__(self):
        return self.now


class Counting(StaticRates):
    def __init__(self, rates):
        super().__init__(rates)
        self.calls = 0

    def get_rate(self, from_ccy, to_ccy):
        self.calls += 1
        return super().get_rate(from_ccy, to_ccy)


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


class Totals(unittest.TestCase):
    def test_exact_cents(self):
        self.assertEqual(invoice_total([LineItem("Pro plan", 1999)], "usd"), 1999)
        for cents in (113, 1155, 1915, 4999, 9999):
            self.assertEqual(invoice_total([LineItem("x", cents)], "usd"), cents)

    def test_tax_rounded_once_per_rate(self):
        lines = [LineItem("Widget", 100, 1, "0.0825")] * 3
        self.assertEqual(invoice_total(lines, "usd"), 325)

    def test_mixed_rates(self):
        lines = [LineItem("Book", 1000, 1, "0"), LineItem("Pen", 250, 2, "0.2"), LineItem("Ink", 333, 3, "0.2")]
        self.assertEqual(invoice_total(lines, "eur"), 1000 + 500 + 999 + 300)

    def test_jpy_and_kwd(self):
        self.assertEqual(invoice_total([LineItem("Plan", 3000), LineItem("Seat", 500, 3, "0.10")], "jpy"), 4650)
        self.assertEqual(invoice_total([LineItem("Plan", 1234, 1, "0.05")], "kwd"), 1296)

    def test_unknown_currency_raises(self):
        with self.assertRaises(ValueError):
            invoice_total([LineItem("Plan", 1000)], "xyz")

    def test_bad_tax_rate_raises(self):
        with self.assertRaises(ValueError):
            invoice_total([LineItem("Plan", 1000, 1, "abc")], "usd")


class Currency(unittest.TestCase):
    def test_exponent(self):
        self.assertEqual([exponent(c) for c in ("usd", "eur", "jpy", "krw", "kwd", "bhd")], [2, 2, 0, 0, 3, 3])
        with self.assertRaises(ValueError):
            exponent("xyz")

    def test_format(self):
        self.assertEqual(format_amount(1999, "usd"), "19.99 USD")
        self.assertEqual(format_amount(4650, "jpy"), "4650 JPY")
        self.assertEqual(format_amount(1234, "kwd"), "1.234 KWD")
        self.assertEqual(format_amount(5, "usd"), "0.05 USD")

    def test_convert_uses_exponents(self):
        rates = StaticRates({"jpy:usd": "0.0067", "kwd:usd": "3.25", "usd:jpy": "149.5", "eur:usd": "1.09"})
        self.assertEqual(convert(50000, "jpy", "usd", rates), 33500)
        self.assertEqual(convert(1234, "kwd", "usd", rates), 401)
        self.assertEqual(convert(1000, "usd", "jpy", rates), 1495)
        self.assertEqual(convert(1000, "eur", "usd", rates), 1090)

    def test_convert_rounds_half_up(self):
        rates = StaticRates({"eur:usd": "1.005"})
        self.assertEqual(convert(100, "eur", "usd", rates), 101)  # 100.5 cents

    def test_cache_keyed_by_pair(self):
        rates = CachedRates(StaticRates({"eur:usd": "1.09", "gbp:usd": "1.27"}), clock=FakeClock())
        self.assertEqual(str(rates.get_rate("eur", "usd")), "1.09")
        self.assertEqual(str(rates.get_rate("gbp", "usd")), "1.27")

    def test_cache_expires(self):
        clock = FakeClock()
        provider = Counting({"eur:usd": "1.09"})
        rates = CachedRates(provider, ttl_seconds=60, clock=clock)
        rates.get_rate("eur", "usd")
        clock.now += 59
        rates.get_rate("eur", "usd")
        self.assertEqual(provider.calls, 1)
        clock.now += 1
        rates.get_rate("eur", "usd")
        self.assertEqual(provider.calls, 2)

    def test_instances_do_not_share(self):
        a = CachedRates(StaticRates({"eur:usd": "1.09"}), clock=FakeClock())
        b = CachedRates(StaticRates({"eur:usd": "2.00"}), clock=FakeClock())
        a.get_rate("eur", "usd")
        self.assertEqual(str(b.get_rate("eur", "usd")), "2.00")


class Processor(unittest.TestCase):
    def setUp(self):
        self.fake = FakeProcessor()
        self.client = ProcessorClient(self.fake)

    def keys(self):
        return [headers.get("Idempotency-Key") for _, _, headers in self.fake.requests]

    def test_timeout_after_processing_charges_once(self):
        self.fake.timeouts = ["after"]
        result = self.client.charge(1999, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.charges), 1)
        self.assertEqual(result.id, "ch_1")

    def test_same_key_on_every_attempt(self):
        self.fake.timeouts = ["before", "after"]
        self.client.charge(1999, "usd", CARD, "in_1")
        keys = self.keys()
        self.assertEqual(len(keys), 3)
        self.assertTrue(keys[0])
        self.assertEqual(len(set(keys)), 1)
        self.assertEqual(len(self.fake.charges), 1)

    def test_different_invoices_different_keys(self):
        self.client.charge(1999, "usd", CARD, "in_1")
        self.client.charge(1999, "usd", CARD, "in_2")
        self.assertEqual(len(set(self.keys())), 2)
        self.assertEqual(len(self.fake.charges), 2)

    def test_at_most_three_attempts(self):
        self.fake.timeouts = ["before"] * 5
        with self.assertRaises(ProcessorError):
            self.client.charge(1999, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.requests), 3)

    def test_decline_is_not_retried(self):
        self.fake.decline_numbers.add(CARD.number)
        with self.assertRaises(CardDeclined):
            self.client.charge(1999, "usd", CARD, "in_1")
        self.assertEqual(len(self.fake.requests), 1)

    def test_card_number_never_logged(self):
        root = logging.getLogger()
        handler, old = Capture(), root.level
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
        try:
            self.fake.timeouts = ["before"]
            self.client.charge(1999, "usd", CARD, "in_1")
            self.fake.decline_numbers.add(CARD.number)
            with self.assertRaises(CardDeclined):
                self.client.charge(1999, "usd", CARD, "in_2")
        finally:
            root.removeHandler(handler)
            root.setLevel(old)
        self.assertFalse([m for m in handler.messages if CARD.number in m])


class Service(unittest.TestCase):
    def setUp(self):
        self.fake = FakeProcessor()
        self.client = ProcessorClient(self.fake)

    def test_decline_marks_failed(self):
        self.fake.decline_numbers.add(CARD.number)
        inv = Invoice("in_1", "cus_1", [LineItem("Plan", 1000)])
        self.assertEqual(bill(inv, CARD, self.client), "failed")

    def test_bad_line_propagates_and_stays_open(self):
        inv = Invoice("in_2", "cus_1", [LineItem("Plan", 1000, 1, "abc")])
        with self.assertRaises(ValueError):
            bill(inv, CARD, self.client)
        self.assertEqual(inv.status, "open")
        self.assertEqual(self.fake.requests, [])

    def test_unknown_currency_stays_open(self):
        inv = Invoice("in_3", "cus_1", [LineItem("Plan", 1000)], currency="xyz")
        with self.assertRaises(ValueError):
            bill(inv, CARD, self.client)
        self.assertEqual(inv.status, "open")

    def test_processor_down_stays_open(self):
        self.fake.timeouts = ["before"] * 3
        inv = Invoice("in_4", "cus_1", [LineItem("Plan", 1000)])
        with self.assertRaises(ProcessorError):
            bill(inv, CARD, self.client)
        self.assertEqual(inv.status, "open")
        self.assertEqual(self.fake.charges, [])

    def test_jpy_charges_exact_amount(self):
        inv = Invoice("in_5", "cus_1", [LineItem("Plan", 3000), LineItem("Seat", 500, 3, "0.10")], currency="jpy")
        self.assertEqual(bill(inv, CARD, self.client), "paid")
        self.assertEqual((self.fake.charges[0]["amount"], self.fake.charges[0]["currency"]), (4650, "jpy"))


if __name__ == "__main__":
    unittest.main()
