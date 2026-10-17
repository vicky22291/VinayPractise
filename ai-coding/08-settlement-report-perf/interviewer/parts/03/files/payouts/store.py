"""Stands in for the payments database. Do not change this file.

Every public method is one database round trip and is counted in `self.calls`.
In production a round trip costs about 1.5 ms, whatever it returns.

Two stores now:
- Store: the primary database. Days up to LIST_LIMIT rows. Rows arrive late, so
  every row gets a sequence number when it is written.
- ArchiveStore: the archive replica used for big days. Merchant and FX tables,
  plus one forward-only cursor per day. No random access.
"""
import bisect
from collections import Counter, defaultdict

LIST_LIMIT = 100_000


class ResultTooLarge(Exception):
    """list_transactions refuses days over LIST_LIMIT rows. Stream them instead."""


class NotSupported(Exception):
    """The archive replica has no random access."""


class _Tables:
    """Merchant and FX tables, shared by both stores."""

    def __init__(self, merchants, fx_rates):
        self._merchants = {m.id: m for m in merchants}
        self._fx = {(r.day, r.base, r.quote): r.rate for r in fx_rates}
        self.calls = Counter()
        self.rows_read = 0  # rows handed out by streaming cursors

    def total_calls(self):
        return sum(self.calls.values())

    def merchant_ids(self):
        self.calls["merchant_ids"] += 1
        return list(self._merchants)

    def get_merchant(self, merchant_id):
        self.calls["get_merchant"] += 1
        return self._merchants[merchant_id]

    def get_merchants(self, merchant_ids):
        """{id: Merchant} for the ids that exist."""
        self.calls["get_merchants"] += 1
        return {i: self._merchants[i] for i in merchant_ids if i in self._merchants}

    def fx_rate(self, base, quote, day):
        self.calls["fx_rate"] += 1
        return self._fx[(day, base, quote)]

    def fx_rates(self, day):
        """{(base, quote): rate} for one day."""
        self.calls["fx_rates"] += 1
        return {(b, q): r for (d, b, q), r in self._fx.items() if d == day}

    def _stream(self, rows):
        for row in rows:
            self.rows_read += 1
            yield row


class Store(_Tables):
    def __init__(self, merchants, transactions, fx_rates):
        super().__init__(merchants, fx_rates)
        self._txns = {}
        self._ids = defaultdict(list)       # (merchant_id, day) -> [txn id]
        self._by_day = defaultdict(list)    # day -> [txn]
        self._seqs = defaultdict(list)      # day -> [seq], parallel to _by_day
        self._next_seq = 1
        for t in transactions:
            self.append(t)

    # -- writes (the payments pipeline calls these, not the report) ------

    def append(self, txn):
        """Write one balance transaction. It gets the next sequence number."""
        self._txns[txn.id] = txn
        self._ids[(txn.merchant_id, txn.day)].append(txn.id)
        self._by_day[txn.day].append(txn)
        self._seqs[txn.day].append(self._next_seq)
        self._next_seq += 1

    def add_merchant(self, merchant):
        self._merchants[merchant.id] = merchant

    # -- reads -----------------------------------------------------------

    def transaction_ids(self, merchant_id, day):
        self.calls["transaction_ids"] += 1
        return list(self._ids.get((merchant_id, day), []))

    def get_transaction(self, txn_id):
        self.calls["get_transaction"] += 1
        return self._txns[txn_id]

    def list_transactions(self, day):
        """Every balance transaction of one day, in insertion order. Refuses big days."""
        self.calls["list_transactions"] += 1
        rows = self._by_day.get(day, [])
        if len(rows) > LIST_LIMIT:
            raise ResultTooLarge(f"{len(rows)} rows for {day}; use iter_transactions")
        return list(rows)

    def iter_transactions(self, day):
        """Stream one day's transactions through a server-side cursor. One round trip."""
        self.calls["iter_transactions"] += 1
        return self._stream(list(self._by_day.get(day, [])))

    def iter_transactions_since(self, day, after_seq):
        """Stream (seq, txn) for one day's rows with seq > after_seq, in seq order. One round trip."""
        self.calls["iter_transactions_since"] += 1
        seqs, rows = self._seqs.get(day, []), self._by_day.get(day, [])
        start = bisect.bisect_right(seqs, after_seq)
        return self._stream(list(zip(seqs[start:], rows[start:])))


class ArchiveStore(_Tables):
    """`source(day)` returns an iterator of BalanceTransaction rows for that day."""

    def __init__(self, merchants, fx_rates, source):
        super().__init__(merchants, fx_rates)
        self._source = source
        self._opened = set()

    def iter_transactions(self, day):
        """One forward-only cursor per day. A second call for the same day raises."""
        self.calls["iter_transactions"] += 1
        if day in self._opened:
            raise RuntimeError(f"cursor for {day} already consumed; the archive cannot rewind")
        self._opened.add(day)
        return self._stream(self._source(day))

    def transaction_ids(self, merchant_id, day):
        raise NotSupported("random access is disabled on the archive replica")

    def get_transaction(self, txn_id):
        raise NotSupported("random access is disabled on the archive replica")

    def list_transactions(self, day):
        raise NotSupported("the archive replica only streams")
