import unittest

from invoicing.currency import CachedRates, StaticRates, convert, exponent, format_amount


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


class CountingRates(StaticRates):
    def __init__(self, rates):
        super().__init__(rates)
        self.calls = 0

    def get_rate(self, from_ccy, to_ccy):
        self.calls += 1
        return super().get_rate(from_ccy, to_ccy)


class CurrencyTest(unittest.TestCase):
    def test_exponent(self):
        self.assertEqual((exponent("usd"), exponent("jpy"), exponent("kwd")), (2, 0, 3))
        with self.assertRaises(ValueError):
            exponent("xyz")

    def test_format(self):
        self.assertEqual(format_amount(1999, "usd"), "19.99 USD")
        self.assertEqual(format_amount(4650, "jpy"), "4650 JPY")
        self.assertEqual(format_amount(1234, "kwd"), "1.234 KWD")

    def test_convert_same_currency(self):
        self.assertEqual(convert(1234, "eur", "eur", None), 1234)

    def test_convert(self):
        rates = StaticRates({"eur:usd": "1.09", "jpy:usd": "0.0067", "kwd:usd": "3.25", "usd:jpy": "149.5"})
        self.assertEqual(convert(1000, "eur", "usd", rates), 1090)
        self.assertEqual(convert(50000, "jpy", "usd", rates), 33500)
        self.assertEqual(convert(1234, "kwd", "usd", rates), 401)
        self.assertEqual(convert(1000, "usd", "jpy", rates), 1495)

    def test_cached_rates_call_provider_once(self):
        provider = CountingRates({"eur:usd": "1.09"})
        rates = CachedRates(provider, clock=Clock())
        for _ in range(5):
            rates.get_rate("eur", "usd")
        self.assertEqual(provider.calls, 1)

    def test_cache_is_per_pair(self):
        rates = CachedRates(StaticRates({"eur:usd": "1.09", "gbp:usd": "1.27"}), clock=Clock())
        self.assertEqual(rates.get_rate("eur", "usd"), "1.09")
        self.assertEqual(rates.get_rate("gbp", "usd"), "1.27")

    def test_cache_expires(self):
        clock, provider = Clock(), CountingRates({"eur:usd": "1.09"})
        rates = CachedRates(provider, ttl_seconds=60, clock=clock)
        rates.get_rate("eur", "usd")
        clock.now = 60
        rates.get_rate("eur", "usd")
        self.assertEqual(provider.calls, 2)

    def test_instances_do_not_share_a_cache(self):
        CachedRates(StaticRates({"eur:usd": "1.09"}), clock=Clock()).get_rate("eur", "usd")
        other = CachedRates(StaticRates({"eur:usd": "2.00"}), clock=Clock())
        self.assertEqual(other.get_rate("eur", "usd"), "2.00")


if __name__ == "__main__":
    unittest.main()
