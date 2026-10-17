"""Field checks for one business record. Kept for callers that validate a single record."""
from kyc.errors import ErrorCollector
from kyc.rules import DEFAULT_RULES


def validate_record(record, rules=None):
    """Return the ValidationErrors for one record from the per-record rules."""
    errors = ErrorCollector()
    for rule in DEFAULT_RULES if rules is None else rules:
        if hasattr(rule, "check"):
            errors.extend(rule.check(record))
    return errors.errors()
