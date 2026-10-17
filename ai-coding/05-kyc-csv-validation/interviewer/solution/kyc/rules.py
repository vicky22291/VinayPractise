"""Validation rules. A rule is any object with check(record) -> [ValidationError].

A file rule also needs to see earlier records. It has begin() -> checker, and
the pipeline calls checker(record, line) for each record of one file, so state
never leaks between files.
"""
import re
from datetime import datetime

from kyc.models import ValidationError
from kyc.schema import COLUMNS, COUNTRIES


class RequiredFields:
    def check(self, record):
        return [ValidationError("MISSING_FIELD", c, f"{c} is required") for c in COLUMNS if not record.get(c)]


class FieldRule:
    """Base for rules on one non-empty field. Subclasses set field, code and ok()."""

    field = code = ""

    def ok(self, value, record):
        raise NotImplementedError

    def message(self, value):
        return f"bad {self.field} {value!r}"

    def check(self, record):
        value = record.get(self.field)
        if value and not self.ok(value, record):
            return [ValidationError(self.code, self.field, self.message(value))]
        return []


class TaxIdFormat(FieldRule):
    field, code = "tax_id", "INVALID_TAX_ID"
    BY_COUNTRY = {
        "US": re.compile(r"\d{2}-\d{7}"),
        "GB": re.compile(r"[A-Z0-9]{8}"),
        "CA": re.compile(r"\d{9}"),
    }
    DEFAULT = re.compile(r"[A-Za-z0-9-]{5,20}")

    def ok(self, value, record):
        return self.BY_COUNTRY.get(record.get("country"), self.DEFAULT).fullmatch(value) is not None


class CountryCode(FieldRule):
    field, code = "country", "INVALID_COUNTRY"

    def ok(self, value, record):
        return value in COUNTRIES


class IncorporationDate(FieldRule):
    field, code = "incorporation_date", "INVALID_DATE"
    SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}")

    def ok(self, value, record):
        # fromisoformat alone would accept 20230115; the shape check pins YYYY-MM-DD.
        if not self.SHAPE.fullmatch(value):
            return False
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return False
        return True


class OwnerEmail(FieldRule):
    field, code = "owner_email", "INVALID_EMAIL"
    SHAPE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

    def ok(self, value, record):
        return self.SHAPE.fullmatch(value) is not None


class ForbiddenWords(FieldRule):
    field, code = "business_name", "FORBIDDEN_WORD"
    WORDS = re.compile(r"\b(bank|test|fake)\b", re.IGNORECASE)

    def ok(self, value, record):
        return self.WORDS.search(value) is None


class MaxLength(FieldRule):
    code = "TOO_LONG"

    def __init__(self, field, limit):
        self.field, self.limit = field, limit

    def ok(self, value, record):
        return len(value) <= self.limit


class DuplicateTaxId:
    def begin(self):
        first_line = {}

        def checker(record, line):
            if not (record.get("country") and record.get("tax_id")):
                return []
            key = (record["country"], record["tax_id"].upper())
            if key in first_line:
                return [ValidationError("DUPLICATE_TAX_ID", "tax_id", f"same tax_id as line {first_line[key]}")]
            first_line[key] = line
            return []

        return checker


class SharedOwner:
    def begin(self):
        seen = {}  # email -> {tax_id: first line}

        def checker(record, line):
            email, tax_id = record.get("owner_email", "").lower(), record.get("tax_id", "").upper()
            if not (email and tax_id):
                return []
            earlier = seen.setdefault(email, {})
            others = [first for tid, first in earlier.items() if tid != tax_id]
            earlier.setdefault(tax_id, line)
            if others:
                return [ValidationError("SHARED_OWNER", "owner_email", f"owner also on line {min(others)}")]
            return []

        return checker


DEFAULT_RULES = [
    RequiredFields(),
    TaxIdFormat(),
    CountryCode(),
    IncorporationDate(),
    OwnerEmail(),
    ForbiddenWords(),
    MaxLength("business_name", 80),
    MaxLength("owner_name", 60),
    DuplicateTaxId(),
    SharedOwner(),
]
