"""Invoice data types. Money is always an int in the smallest currency unit."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LineItem:
    description: str
    unit_amount: int
    quantity: int = 1
    tax_rate: str = "0"  # decimal string, e.g. "0.0825"


@dataclass(frozen=True)
class Card:
    number: str
    exp_month: int
    exp_year: int

    @property
    def last4(self):
        return self.number[-4:]


@dataclass
class Invoice:
    id: str
    customer_id: str
    lines: list = field(default_factory=list)
    currency: str = "usd"
    status: str = "open"  # open -> paid | failed
    charge_id: str | None = None
