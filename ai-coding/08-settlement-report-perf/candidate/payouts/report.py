"""Daily settlement report.

One line per merchant and currency the merchant took payments in that day, then
one TOTAL line per payout currency. Finance reconciles payouts against this file
byte for byte, so its format must not change.
"""
from collections import namedtuple

from payouts.fx import convert
from payouts.models import CHARGE, DISPUTE, REFUND

HEADER = ("merchant_id,merchant_name,currency,count,charges,refunds,disputes,"
          "fees,net,payout_currency,payout_amount")
CURRENCIES = ["usd", "eur", "gbp", "cad", "aud", "sgd"]

Line = namedtuple("Line", "merchant_id merchant_name currency count charges refunds "
                          "disputes fees net payout_currency payout_amount")


def build_report(store, day):
    lines = []
    totals = []  # [payout_currency, amount] pairs
    for merchant_id in store.merchant_ids():
        merchant = store.get_merchant(merchant_id)
        for currency in CURRENCIES:
            line = _line_for(store, merchant, currency, day)
            if line is None:
                continue
            lines.append(line)
            lines.sort()
            _add_total(totals, line.payout_currency, line.payout_amount)

    out = HEADER + "\n"
    for line in lines:
        out += _format(line) + "\n"
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
        if txn.type == CHARGE:
            charges += txn.amount
        elif txn.type == REFUND:
            refunds -= txn.amount
        elif txn.type == DISPUTE:
            disputes -= txn.amount
        fees += txn.fee
        payout += convert(store, txn.amount - txn.fee, txn.currency, merchant.payout_currency, day)
    if count == 0:
        return None
    net = charges - refunds - disputes - fees
    return Line(merchant.id, merchant.name, currency, count, charges, refunds, disputes,
                fees, net, merchant.payout_currency, payout)


def _add_total(totals, currency, amount):
    for pair in totals:
        if pair[0] == currency:
            pair[1] += amount
            return
    totals.append([currency, amount])


def _format(line):
    return (f"{line.merchant_id},{line.merchant_name},{line.currency},{line.count},"
            f"{line.charges},{line.refunds},{line.disputes},{line.fees},{line.net},"
            f"{line.payout_currency},{line.payout_amount}")
