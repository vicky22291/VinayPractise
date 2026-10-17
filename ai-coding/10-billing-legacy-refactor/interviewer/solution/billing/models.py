"""Billing data types. Money is an int in cents. Dates are datetime.date."""
from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    unit_amount: int  # cents per seat per month
    setup_fee: int = 0  # cents, charged once on the first invoice
    usage_unit_amount: int = 0  # cents per metered unit, 0 = not metered


@dataclass(frozen=True)
class Coupon:
    id: str
    duration: str  # once | repeating | forever
    percent_off: int = 0
    amount_off: int = 0  # cents
    duration_in_months: int = 0


@dataclass(frozen=True)
class Subscription:
    id: str
    customer_id: str
    plan_id: str
    quantity: int
    start: date
    trial_end: date | None = None
    coupon_id: str | None = None
    tax_rate: str = "0"  # decimal string, e.g. "0.0825"


@dataclass(frozen=True)
class Event:
    kind: str  # plan_change | quantity_change | cancel | usage
    at: date
    plan_id: str | None = None
    quantity: int | None = None


@dataclass
class Line:
    description: str
    amount: int


@dataclass
class Invoice:
    subscription_id: str
    period_start: date
    period_end: date
    lines: list = field(default_factory=list)
    subtotal: int = 0
    discount: int = 0
    tax: int = 0
    total: int = 0
