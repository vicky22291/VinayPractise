"""Collect the validation errors for one record."""
from kyc.models import ValidationError


class ErrorCollector:
    """Accumulates errors in order. Adding the same (code, field) twice keeps one copy."""

    def __init__(self):
        self._errors = []
        self._seen = set()

    def add(self, code, field, message):
        if (code, field) not in self._seen:
            self._seen.add((code, field))
            self._errors.append(ValidationError(code, field, message))

    def extend(self, errors):
        for e in errors:
            self.add(e.code, e.field, e.message)

    def __len__(self):
        return len(self._errors)

    def errors(self):
        return list(self._errors)
