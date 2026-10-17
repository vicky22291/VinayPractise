"""Records read from the payments database. Amounts are integers in minor units (cents)."""
from dataclasses import dataclass
from decimal import Decimal

CHARGE = "charge"
REFUND = "refund"
DISPUTE = "dispute"


@dataclass(frozen=True, slots=True)
class Merchant:
    id: str
    name: str
    payout_currency: str


@dataclass(frozen=True, slots=True)
class BalanceTransaction:
    id: str
    merchant_id: str
    type: str        # charge, refund or dispute
    amount: int      # signed: charges positive, refunds and disputes negative
    fee: int         # what we keep, never negative
    currency: str
    day: str         # YYYY-MM-DD, UTC


@dataclass(frozen=True, slots=True)
class FxRate:
    day: str
    base: str
    quote: str
    rate: Decimal    # 1 minor unit of base = rate minor units of quote
