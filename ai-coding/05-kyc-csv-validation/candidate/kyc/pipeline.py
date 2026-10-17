"""Validate a whole CSV export."""
from kyc.csv_reader import read_rows
from kyc.models import RecordResult, ValidationError
from kyc.validators import validate_record


def _record_id(header, values):
    index = header.index("record_id")
    return values[index] if index < len(values) else ""


def validate_csv(text):
    """Return one RecordResult per data row, in file order."""
    header, rows = read_rows(text)
    results = []
    for line, values in rows:
        if len(values) != len(header):
            error = ValidationError(
                "WRONG_COLUMN_COUNT", "*", f"expected {len(header)} fields, got {len(values)}"
            )
            results.append(RecordResult(line, _record_id(header, values), [error]))
            continue
        record = dict(zip(header, values))
        results.append(RecordResult(line, record["record_id"], validate_record(record)))
    return results
