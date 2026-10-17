"""Field checks for one business record."""
import re

from kyc.errors import ErrorCollector
from kyc.schema import COLUMNS, COUNTRIES

TAX_ID_RE = re.compile(r"^[A-Za-z0-9-]{5,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _is_date(value):
    m = DATE_RE.match(value)
    if not m:
        return False
    _, month, day = (int(g) for g in m.groups())
    return 1 <= month <= 12 and 1 <= day <= 31


def validate_record(record):
    """Return the list of ValidationErrors for one record (a dict of column -> value)."""
    errors = ErrorCollector()
    for column in COLUMNS:
        if not record.get(column):
            errors.add("MISSING_FIELD", column, f"{column} is required")

    tax_id = record.get("tax_id")
    if tax_id and not TAX_ID_RE.match(tax_id):
        errors.add("INVALID_TAX_ID", "tax_id", f"bad tax id {tax_id!r}")

    country = record.get("country")
    if country and country not in COUNTRIES:
        errors.add("INVALID_COUNTRY", "country", f"unsupported country {country!r}")

    date = record.get("incorporation_date")
    if date and not _is_date(date):
        errors.add("INVALID_DATE", "incorporation_date", f"bad date {date!r}, want YYYY-MM-DD")

    email = record.get("owner_email")
    if email and not EMAIL_RE.match(email):
        errors.add("INVALID_EMAIL", "owner_email", f"bad email {email!r}")
    return errors.errors()
