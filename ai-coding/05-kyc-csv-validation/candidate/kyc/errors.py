"""Collect the validation errors for one record."""
from kyc.models import ValidationError


class ErrorCollector:
    """Accumulates errors. Adding the same error twice keeps one copy."""

    def __init__(self):
        self._errors = {}

    def add(self, code, field, message):
        self._errors[code] = ValidationError(code, field, message)

    def __len__(self):
        return len(self._errors)

    def errors(self):
        return list(self._errors.values())
