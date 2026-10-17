import unittest

from invoicing.currency import CachedRates, StaticRates, convert, format_amount


class CountingRates(StaticRates):
    def __init__(self, rates):
        super().__init__(rates)
        self.calls = 0

    def get_rate(self, from_ccy, to_ccy):
        self.calls += 1
        return super().get_rate(from_ccy, to_ccy)


class CurrencyTest(unittest.TestCase):
    def test_format_usd(self):
        self.assertEqual(format_amount(2099, "usd"), "20.99 USD")

    def test_convert_same_currency(self):
        self.assertEqual(convert(1234, "eur", "eur", None), 1234)

    def test_convert_eur_to_usd(self):
        rates = StaticRates({"eur:usd": "1.09"})
        self.assertEqual(convert(1000, "eur", "usd", rates), 1090)

    def test_cached_rates_call_provider_once(self):
        provider = CountingRates({"eur:usd": "1.09"})
        rates = CachedRates(provider)
        for _ in range(5):
            rates.get_rate("eur", "usd")
        self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
