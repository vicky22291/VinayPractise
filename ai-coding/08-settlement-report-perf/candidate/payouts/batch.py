"""Turn the settlement report into payout instructions.

This reads the report text exactly as finance stores it. Names may contain
commas, so fields are taken from both ends of each line.
"""
from dataclasses import dataclass

MINIMUM_PAYOUT = {"usd": 100, "eur": 100, "gbp": 100, "cad": 100, "aud": 100, "sgd": 100}


@dataclass(frozen=True)
class Instruction:
    merchant_id: str
    currency: str
    amount: int


def parse_lines(report_text):
    """Yield (merchant_id, payout_currency, payout_amount) per merchant line. Skips the header and TOTALs."""
    for i, line in enumerate(report_text.splitlines()):
        if i == 0 or not line or line.startswith("TOTAL,"):
            continue
        fields = line.split(",")
        yield fields[0], fields[-2], int(fields[-1])


def instructions(report_text, carried=None):
    """Sum each merchant's lines per payout currency.

    Returns (instructions, carried): amounts below the minimum, or negative, are
    carried to the next day instead of paid.
    """
    totals = dict(carried or {})
    for merchant_id, currency, amount in parse_lines(report_text):
        key = (merchant_id, currency)
        totals[key] = totals.get(key, 0) + amount
    pay, carry = [], {}
    for (merchant_id, currency), amount in sorted(totals.items()):
        if amount >= MINIMUM_PAYOUT[currency]:
            pay.append(Instruction(merchant_id, currency, amount))
        elif amount != 0:
            carry[(merchant_id, currency)] = amount
    return pay, carry
