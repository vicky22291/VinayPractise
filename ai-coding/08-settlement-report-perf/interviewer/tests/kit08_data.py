"""Hidden datasets for kit 08. Different seeds, rates and shapes from payouts/sample.py."""
import random
from decimal import Decimal

from payouts.models import BalanceTransaction, FxRate, Merchant

DAY = "2026-10-14"
CURRENCIES = ["usd", "eur", "gbp", "cad", "aud", "sgd"]
USD_VALUE = {"usd": 1.0, "eur": 1.0779, "gbp": 1.2988, "cad": 0.7114, "aud": 0.6421, "sgd": 0.7533}
NAMES = ["Cedar Books", "Smith, Jones & Co", "Harbor Coffee", 'The "Best" Shop', "Orbit Labs",
         "Maple Supply", "Tide Studio", "Kite Market", "Grove Goods", "Iris Tools"]


def fx_rates(day=DAY):
    out = []
    for base in CURRENCIES:
        for quote in CURRENCIES:
            if base != quote:
                rate = Decimal(USD_VALUE[base] / USD_VALUE[quote]).quantize(Decimal("0.000001"))
                out.append(FxRate(day, base, quote, rate))
    return out


def merchants(count, seed):
    rng = random.Random(seed)
    ids = rng.sample(range(10**7, 10**8), count)  # random order: iteration order is not sorted order
    return [Merchant(f"acct_{i}", rng.choice(NAMES), rng.choice(["usd", "usd", "eur", "gbp", "cad"])) for i in ids]


def transactions(merchant_list, count, seed, day=DAY, orphans=True, other_day=True):
    """Yields `count` rows. Some belong to merchants missing from the table, some to another day."""
    rng = random.Random(seed)
    for i in range(count):
        roll = rng.random()
        if orphans and roll < 0.0005:
            merchant_id, payout = "acct_deleted", "usd"
        else:
            m = rng.choice(merchant_list)
            merchant_id, payout = m.id, m.payout_currency
        currency = payout if rng.random() < 0.6 else rng.choice(CURRENCIES)
        txn_day = "2026-10-13" if other_day and rng.random() < 0.01 else day
        kind = rng.random()
        if kind < 0.85:
            amount = rng.randint(50, 80_000)
            yield BalanceTransaction(f"txn_{seed}_{i:08d}", merchant_id, "charge", amount,
                                     amount * 29 // 1000 + 30, currency, txn_day)
        elif kind < 0.98:
            yield BalanceTransaction(f"txn_{seed}_{i:08d}", merchant_id, "refund", -rng.randint(50, 30_000),
                                     0, currency, txn_day)
        else:
            yield BalanceTransaction(f"txn_{seed}_{i:08d}", merchant_id, "dispute", -rng.randint(500, 60_000),
                                     1_500, currency, txn_day)


P1 = dict(merchants=400, mseed=11, txns=60_000, tseed=12)
P2 = dict(merchants=1_500, mseed=21, txns=300_000, tseed=22, other_day=False)  # an archive cursor is per day
