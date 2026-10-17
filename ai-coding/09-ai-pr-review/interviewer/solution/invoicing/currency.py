"""Currency helpers for multi-currency invoices.

Amounts are ints in the currency's minor unit. Rates are decimal strings, major
unit to major unit ("1 JPY = 0.0067 USD").
"""
import json
import time
from decimal import ROUND_HALF_UP, Decimal

EXPONENTS = {"usd": 2, "eur": 2, "gbp": 2, "cad": 2, "inr": 2, "jpy": 0, "krw": 0, "kwd": 3, "bhd": 3}
SUPPORTED = set(EXPONENTS)


def exponent(currency):
    """Digits after the decimal point: 2 for usd, 0 for jpy, 3 for kwd."""
    try:
        return EXPONENTS[currency]
    except KeyError:
        raise ValueError(f"unsupported currency {currency!r}") from None


def format_amount(amount, currency):
    """Human-readable amount for invoice emails, e.g. '19.99 USD' or '4650 JPY'."""
    exp = exponent(currency)
    return f"{Decimal(amount).scaleb(-exp):.{exp}f} {currency.upper()}"


class StaticRates:
    """Rate provider backed by a dict like {"jpy:usd": "0.0067"}."""

    def __init__(self, rates):
        self.rates = rates

    @classmethod
    def from_file(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def get_rate(self, from_ccy, to_ccy):
        return self.rates[f"{from_ccy}:{to_ccy}"]


class CachedRates:
    """Caches rates per currency pair for ttl_seconds, so we do not call the provider per invoice."""

    def __init__(self, provider, ttl_seconds=3600, clock=time.monotonic):
        self.provider = provider
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._cache = {}  # (from_ccy, to_ccy) -> (rate, fetched_at)

    def get_rate(self, from_ccy, to_ccy):
        key, now = (from_ccy, to_ccy), self.clock()
        hit = self._cache.get(key)
        if hit is None or now - hit[1] >= self.ttl_seconds:
            hit = (self.provider.get_rate(from_ccy, to_ccy), now)
            self._cache[key] = hit
        return hit[0]


def convert(amount, from_ccy, to_ccy, rates):
    """Convert minor units of from_ccy into minor units of to_ccy, rounded half up."""
    if from_ccy == to_ccy:
        exponent(from_ccy)
        return amount
    major = Decimal(amount).scaleb(-exponent(from_ccy)) * Decimal(rates.get_rate(from_ccy, to_ccy))
    return int(major.scaleb(exponent(to_ccy)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
