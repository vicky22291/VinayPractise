"""Daily settlement report.

One line per merchant and currency the merchant took payments in that day, then
one TOTAL line per payout currency. Finance reconciles payouts against this file
byte for byte, so its format must not change.

One pass over the day's transactions, O(N + M log M), a constant number of round trips:
merchant table, FX table, one streaming cursor.

Each transaction is converted and rounded on its own, then summed. That is what
the ledger does when it books the transaction, and it is what keeps payouts
equal to the ledger. Summing first and rounding once moves totals by cents.
"""
from collections import namedtuple

from payouts.fx import convert_at
from payouts.models import CHARGE, DISPUTE, REFUND

HEADER = ("merchant_id,merchant_name,currency,count,charges,refunds,disputes,"
          "fees,net,payout_currency,payout_amount")
CURRENCIES = ["usd", "eur", "gbp", "cad", "aud", "sgd"]

Line = namedtuple("Line", "merchant_id merchant_name currency count charges refunds "
                          "disputes fees net payout_currency payout_amount")

# Accumulator slots per (merchant_id, currency).
COUNT, CHARGES, REFUNDS, DISPUTES, FEES, PAYOUT = range(6)


def build_report(store, day):
    merchants = store.get_merchants(store.merchant_ids())
    rates = store.fx_rates(day)
    acc = {}
    for txn in store.iter_transactions(day):
        _add(acc, txn, merchants, rates)
    return render(acc, merchants)


def _add(acc, txn, merchants, rates):
    """Fold one transaction into acc. Same rules as the original per-merchant loop."""
    merchant = merchants.get(txn.merchant_id)
    if merchant is None or txn.currency not in CURRENCIES:
        return  # the original only reported merchants in the table, in these currencies
    row = acc.get((txn.merchant_id, txn.currency))
    if row is None:
        row = acc[(txn.merchant_id, txn.currency)] = [0, 0, 0, 0, 0, 0]
    row[COUNT] += 1
    if txn.type == CHARGE:
        row[CHARGES] += txn.amount
    elif txn.type == REFUND:
        row[REFUNDS] -= txn.amount
    elif txn.type == DISPUTE:
        row[DISPUTES] -= txn.amount
    row[FEES] += txn.fee
    net = txn.amount - txn.fee
    if txn.currency == merchant.payout_currency:
        row[PAYOUT] += net
    else:
        row[PAYOUT] += convert_at(net, rates[(txn.currency, merchant.payout_currency)])


def render(acc, merchants):
    """acc: {(merchant_id, currency): [count, charges, refunds, disputes, fees, payout]}."""
    parts = [HEADER]
    totals = {}
    for (merchant_id, currency) in sorted(acc):
        c, ch, rf, dp, fe, po = acc[(merchant_id, currency)]
        name, payout_currency = merchants[merchant_id].name, merchants[merchant_id].payout_currency
        parts.append(_format(Line(merchant_id, name, currency, c, ch, rf, dp, fe,
                                  ch - rf - dp - fe, payout_currency, po)))
        totals[payout_currency] = totals.get(payout_currency, 0) + po
    for currency in sorted(totals):
        parts.append(f"TOTAL,,,,,,,,,{currency},{totals[currency]}")
    return "\n".join(parts) + "\n"


def _format(line):
    return (f"{line.merchant_id},{line.merchant_name},{line.currency},{line.count},"
            f"{line.charges},{line.refunds},{line.disputes},{line.fees},{line.net},"
            f"{line.payout_currency},{line.payout_amount}")


# -- incremental runs (Part 3) ----------------------------------------------

def run_incremental(store, day, checkpoint):
    """Fold only rows written since `checkpoint`. Returns (report, new_checkpoint).

    The checkpoint is plain JSON: the day, the last sequence number folded in, the
    accumulator, and name plus payout currency of every merchant seen. Per-line
    rounding makes the accumulator additive, which is what makes this possible.
    """
    if checkpoint is None:
        checkpoint = {"day": day, "seq": 0, "lines": {}, "merchants": {}}
    if checkpoint["day"] != day:
        raise ValueError(f"checkpoint is for {checkpoint['day']}, not {day}")

    new = list(store.iter_transactions_since(day, checkpoint["seq"]))
    if not new:
        return render(_load(checkpoint), _merchants_of(checkpoint)), checkpoint

    known = _merchants_of(checkpoint)
    missing = {t.merchant_id for _, t in new} - set(known)
    if missing:
        known.update(store.get_merchants(sorted(missing)))
    rates = store.fx_rates(day)
    acc = _load(checkpoint)
    for _, txn in new:
        _add(acc, txn, known, rates)

    seen = {m for m, _ in acc}
    result = {
        "day": day,
        "seq": new[-1][0],
        "lines": {f"{m}|{c}": row for (m, c), row in acc.items()},
        "merchants": {m: [known[m].name, known[m].payout_currency] for m in sorted(seen)},
    }
    return render(acc, known), result


def _load(checkpoint):
    out = {}
    for key, row in checkpoint["lines"].items():
        merchant_id, currency = key.rsplit("|", 1)
        out[(merchant_id, currency)] = list(row)
    return out


class _Known:
    __slots__ = ("name", "payout_currency")

    def __init__(self, name, payout_currency):
        self.name, self.payout_currency = name, payout_currency


def _merchants_of(checkpoint):
    return {m: _Known(name, cur) for m, (name, cur) in checkpoint["merchants"].items()}
