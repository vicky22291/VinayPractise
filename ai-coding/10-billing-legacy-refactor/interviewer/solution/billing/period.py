"""The billing period: the calendar month containing as_of, as [start, end)."""
from datetime import date


def billing_period(as_of):
    start = date(as_of.year, as_of.month, 1)
    end = date(as_of.year + 1, 1, 1) if as_of.month == 12 else date(as_of.year, as_of.month + 1, 1)
    return start, end


def months_between(earlier, later):
    """Whole calendar months from earlier's month to later's month."""
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)
