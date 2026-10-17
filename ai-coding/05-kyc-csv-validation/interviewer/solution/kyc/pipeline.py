"""Validate a CSV export, whole or streamed."""
import io

from kyc.csv_reader import iter_rows
from kyc.errors import ErrorCollector
from kyc.models import RecordResult, ValidationError
from kyc.rules import DEFAULT_RULES


def _checkers(rules):
    out = []
    for rule in rules:
        if hasattr(rule, "begin"):
            out.append(rule.begin())
        else:
            out.append(lambda record, line, rule=rule: rule.check(record))
    return out


def validate_stream(lines, rules=None):
    """Yield one RecordResult per data row, in file order, reading lazily."""
    header, rows = iter_rows(lines)
    width, id_index = len(header), header.index("record_id")
    checkers = _checkers(DEFAULT_RULES if rules is None else rules)
    for line, values in rows:
        record_id = values[id_index] if id_index < len(values) else ""
        if len(values) != width:
            error = ValidationError("WRONG_COLUMN_COUNT", "*", f"expected {width} fields, got {len(values)}")
            yield RecordResult(line, record_id, [error])
            continue
        record = dict(zip(header, values))
        errors = ErrorCollector()
        for check in checkers:
            errors.extend(check(record, line))
        yield RecordResult(line, record_id, errors.errors())


def validate_csv(text, rules=None):
    """Return one RecordResult per data row, in file order."""
    return list(validate_stream(io.StringIO(text, newline=""), rules))
