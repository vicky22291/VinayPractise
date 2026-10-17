"""Stands in for the payments database. Do not change this file.

Every public method is one database round trip and is counted in `self.calls`.
In production a round trip costs about 1.5 ms, whatever it returns.
"""
from collections import Counter, defaultdict


class Store:
    def __init__(self, merchants, transactions, fx_rates):
        self._merchants = {m.id: m for m in merchants}
        self._txns = {}
        self._ids = defaultdict(list)       # (merchant_id, day) -> [txn id]
        self._by_day = defaultdict(list)    # day -> [txn]
        for t in transactions:
            self._txns[t.id] = t
            self._ids[(t.merchant_id, t.day)].append(t.id)
            self._by_day[t.day].append(t)
        self._fx = {(r.day, r.base, r.quote): r.rate for r in fx_rates}
        self.calls = Counter()

    def total_calls(self):
        return sum(self.calls.values())

    # -- point lookups ---------------------------------------------------

    def merchant_ids(self):
        self.calls["merchant_ids"] += 1
        return list(self._merchants)

    def get_merchant(self, merchant_id):
        self.calls["get_merchant"] += 1
        return self._merchants[merchant_id]

    def transaction_ids(self, merchant_id, day):
        self.calls["transaction_ids"] += 1
        return list(self._ids.get((merchant_id, day), []))

    def get_transaction(self, txn_id):
        self.calls["get_transaction"] += 1
        return self._txns[txn_id]

    def fx_rate(self, base, quote, day):
        self.calls["fx_rate"] += 1
        return self._fx[(day, base, quote)]

    # -- bulk reads ------------------------------------------------------

    def get_merchants(self, merchant_ids):
        """{id: Merchant} for the ids that exist."""
        self.calls["get_merchants"] += 1
        return {i: self._merchants[i] for i in merchant_ids if i in self._merchants}

    def list_transactions(self, day):
        """Every balance transaction of one day, in insertion order."""
        self.calls["list_transactions"] += 1
        return list(self._by_day.get(day, []))

    def fx_rates(self, day):
        """{(base, quote): rate} for one day."""
        self.calls["fx_rates"] += 1
        return {(b, q): r for (d, b, q), r in self._fx.items() if d == day}
