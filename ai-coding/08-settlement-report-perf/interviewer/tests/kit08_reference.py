"""The starter's report algorithm, kept verbatim as the oracle for random datasets.
Works with any store that still offers the point lookups (in-memory Store)."""
from collections import namedtuple
from decimal import ROUND_HALF_EVEN, Decimal

HEADER = ("merchant_id,merchant_name,currency,count,charges,refunds,disputes,"
          "fees,net,payout_currency,payout_amount")
CURRENCIES = ["usd", "eur", "gbp", "cad", "aud", "sgd"]
Line = namedtuple("Line", "merchant_id merchant_name currency count charges refunds "
                          "disputes fees net payout_currency payout_amount")


def convert(store, amount, base, quote, day):
    if base == quote:
        return amount
    rate = store.fx_rate(base, quote, day)
    return int((Decimal(amount) * rate).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def build_report(store, day):
    lines, totals = [], []
    for merchant_id in store.merchant_ids():
        merchant = store.get_merchant(merchant_id)
        for currency in CURRENCIES:
            line = _line_for(store, merchant, currency, day)
            if line is None:
                continue
            lines.append(line)
            lines.sort()
            for pair in totals:
                if pair[0] == line.payout_currency:
                    pair[1] += line.payout_amount
                    break
            else:
                totals.append([line.payout_currency, line.payout_amount])
    out = HEADER + "\n"
    for l in lines:
        out += (f"{l.merchant_id},{l.merchant_name},{l.currency},{l.count},{l.charges},{l.refunds},"
                f"{l.disputes},{l.fees},{l.net},{l.payout_currency},{l.payout_amount}\n")
    for currency, amount in sorted(totals):
        out += f"TOTAL,,,,,,,,,{currency},{amount}\n"
    return out


def _line_for(store, merchant, currency, day):
    count = charges = refunds = disputes = fees = payout = 0
    for txn_id in store.transaction_ids(merchant.id, day):
        txn = store.get_transaction(txn_id)
        if txn.currency != currency:
            continue
        count += 1
        if txn.type == "charge":
            charges += txn.amount
        elif txn.type == "refund":
            refunds -= txn.amount
        elif txn.type == "dispute":
            disputes -= txn.amount
        fees += txn.fee
        payout += convert(store, txn.amount - txn.fee, txn.currency, merchant.payout_currency, day)
    if count == 0:
        return None
    return Line(merchant.id, merchant.name, currency, count, charges, refunds, disputes,
                fees, charges - refunds - disputes - fees, merchant.payout_currency, payout)
