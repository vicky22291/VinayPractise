"""Currency helpers for multi-currency invoices."""
import json

SUPPORTED = {"usd", "eur", "gbp", "cad", "inr", "jpy", "krw", "kwd", "bhd"}


def format_amount(amount, currency):
    """Human-readable amount for invoice emails, e.g. '20.99 USD'."""
    return f"{amount / 100:.2f} {currency.upper()}"


class StaticRates:
    """Rate provider backed by a dict like {"jpy:usd": "0.0067"} (major unit to major unit)."""

    def __init__(self, rates):
        self.rates = rates

    @classmethod
    def from_file(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def get_rate(self, from_ccy, to_ccy):
        return self.rates[f"{from_ccy}:{to_ccy}"]


class CachedRates:
    """Caches rates from a provider so we do not call it once per invoice."""

    def __init__(self, provider, ttl_seconds=3600, cache={}):
        self.provider = provider
        self.ttl_seconds = ttl_seconds
        self.cache = cache

    def get_rate(self, from_ccy, to_ccy):
        if to_ccy not in self.cache:
            self.cache[to_ccy] = self.provider.get_rate(from_ccy, to_ccy)
        return self.cache[to_ccy]


def convert(amount, from_ccy, to_ccy, rates):
    """Convert minor units of from_ccy into minor units of to_ccy for settlement reports."""
    if from_ccy == to_ccy:
        return amount
    rate = float(rates.get_rate(from_ccy, to_ccy))
    return round(amount / 100 * rate * 100)
