"""Money: an int amount in minor units plus its currency. Floats cannot get in."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from invoicing.currency import exponent, format_amount


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str

    def __post_init__(self):
        if type(self.amount) is not int:
            raise TypeError(f"Money amount must be int minor units, got {type(self.amount).__name__}")
        exponent(self.currency)

    @classmethod
    def from_major(cls, value, currency):
        """Money.from_major("19.99", "usd") == Money(1999, "usd"). Floats are refused."""
        if not isinstance(value, (str, Decimal)):
            raise TypeError(f"from_major takes str or Decimal, got {type(value).__name__}")
        try:
            major = Decimal(value)
        except InvalidOperation:
            raise ValueError(f"not a number: {value!r}") from None
        minor = major.scaleb(exponent(currency))
        if not minor.is_finite() or minor != minor.to_integral_value():
            raise ValueError(f"{value!r} has more decimal places than {currency} allows")
        return cls(int(minor), currency)

    def _same_currency(self, other):
        if other.currency != self.currency:
            raise ValueError(f"cannot mix {self.currency} and {other.currency}")

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor):
        if type(factor) is not int:
            return NotImplemented
        return Money(self.amount * factor, self.currency)

    __rmul__ = __mul__

    def __str__(self):
        return format_amount(self.amount, self.currency)
