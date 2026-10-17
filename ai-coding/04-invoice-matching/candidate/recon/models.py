"""Payments, invoices and the matches between them."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Invoice:
    id: str
    amount: float
    due_date: date


@dataclass(frozen=True)
class Payment:
    id: str
    amount: float
    memo: str


@dataclass(frozen=True)
class Match:
    payment: Payment
    invoice: Invoice | None  # None when nothing matched
