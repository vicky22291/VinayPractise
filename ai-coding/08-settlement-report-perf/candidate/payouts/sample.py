"""Seeded sample data, so the report can be run without a database."""
import random
from decimal import Decimal

from payouts.models import CHARGE, DISPUTE, REFUND, BalanceTransaction, FxRate, Merchant

CURRENCIES = ["usd", "eur", "gbp", "cad", "aud", "sgd"]
USD_VALUE = {"usd": 1.0, "eur": 1.0841, "gbp": 1.2713, "cad": 0.7262, "aud": 0.6544, "sgd": 0.7419}
WORDS = ["Acme", "Blue", "Cedar", "Delta", "Echo", "Fern", "Grove", "Harbor", "Iris", "Juniper",
         "Kite", "Lumen", "Maple", "North", "Orbit", "Pine", "Quill", "River", "Stone", "Tide"]
KINDS = ["Books", "Coffee", "Labs", "Tools", "Supply", "Studio", "Market", "Goods"]


def fx_rates(day):
    rates = []
    for base in CURRENCIES:
        for quote in CURRENCIES:
            if base != quote:
                rate = Decimal(USD_VALUE[base] / USD_VALUE[quote]).quantize(Decimal("0.000001"))
                rates.append(FxRate(day, base, quote, rate))
    return rates


def merchants(count, seed=1):
    rng = random.Random(seed)
    out = []
    for i in range(count):
        name = f"{rng.choice(WORDS)} {rng.choice(KINDS)}"
        out.append(Merchant(f"acct_{rng.randrange(10**8):08d}", name, rng.choice(["usd", "usd", "eur", "gbp"])))
    return out


def transactions(merchant_list, count, day, seed=2):
    rng = random.Random(seed)
    for i in range(count):
        m = rng.choice(merchant_list)
        currency = m.payout_currency if rng.random() < 0.7 else rng.choice(CURRENCIES)
        roll = rng.random()
        if roll < 0.85:
            amount = rng.randint(100, 50_000)
            yield BalanceTransaction(f"txn_{i:08d}", m.id, CHARGE, amount, amount * 29 // 1000 + 30, currency, day)
        elif roll < 0.98:
            yield BalanceTransaction(f"txn_{i:08d}", m.id, REFUND, -rng.randint(100, 20_000), 0, currency, day)
        else:
            yield BalanceTransaction(f"txn_{i:08d}", m.id, DISPUTE, -rng.randint(1_000, 50_000), 1_500, currency, day)
