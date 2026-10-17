"""Reports for ops: a text summary, a JSON document for the dashboard, and an
errors CSV that the ops queue imports."""
import csv
import io
import json

from kyc.schema import ERROR_CODES, SEVERITY


def _counts(results):
    valid = sum(1 for r in results if r.valid)
    return len(results), valid, len(results) - valid


def format_report(results):
    total, valid, invalid = _counts(results)
    lines = [f"{total} records: {valid} valid, {invalid} invalid"]
    for r in results:
        for e in r.errors:
            lines.append(f"line {r.line} ({r.record_id or '?'}): {e.code} {e.field}: {e.message}")
    return "\n".join(lines)


def to_json(results):
    """Dashboard payload. Records are listed only when they have errors."""
    total, valid, invalid = _counts(results)
    return json.dumps(
        {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "records": [
                {
                    "line": r.line,
                    "record_id": r.record_id,
                    "errors": [
                        {"code": e.code, "field": e.field, "message": e.message, "help": ERROR_CODES.get(e.code, "")}
                        for e in r.errors
                    ],
                }
                for r in results
                if not r.valid
            ],
        },
        indent=2,
    )


def to_error_csv(results):
    """One row per error, most urgent first, for the ops queue import."""
    rows = [
        (SEVERITY.get(e.code, 9), r.line, r.record_id, e.code, e.field, e.message)
        for r in results
        for e in r.errors
    ]
    rows.sort(key=lambda row: (row[0], row[1]))
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["severity", "line", "record_id", "code", "field", "message"])
    writer.writerows(rows)
    return out.getvalue()
