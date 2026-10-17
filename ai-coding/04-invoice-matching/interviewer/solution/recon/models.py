"""Payments, invoices and the matches between them. Amounts are integer cents."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Invoice:
    id: str
    amount: int
    due_date: date
    position: int = 0  # index in the invoice list: the last tie-break


@dataclass(frozen=True)
class Payment:
    id: str
    amount: int
    memo: str


@dataclass(frozen=True)
class Match:
    payment: Payment
    invoices: tuple  # () when nothing matched, several for a multi-invoice memo
    tier: str | None = None  # "memo", "amount", or None

    @property
    def invoice(self):
        return self.invoices[0] if self.invoices else None

    @property
    def difference(self):
        """Invoice total minus payment amount. Positive means forgiven."""
        return sum(inv.amount for inv in self.invoices) - self.payment.amount
