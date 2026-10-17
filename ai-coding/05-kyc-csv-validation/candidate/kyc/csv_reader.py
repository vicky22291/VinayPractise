"""Read the verification CSV text into a header and data rows."""
from kyc.schema import COLUMNS


class HeaderError(ValueError):
    """The header row is missing a required column."""


def _split(line):
    return [value.strip(' "') for value in line.split(",")]


def read_rows(text):
    """Return (header, rows).

    header is the list of column names. rows is a list of (line, values)
    tuples, one per data row, where line is the 1-based line number in the
    file (the header is line 1).
    """
    lines = text.split("\n")
    header = _split(lines[0])
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise HeaderError("missing columns: " + ", ".join(missing))
    rows = [(number, _split(line)) for number, line in enumerate(lines[1:], start=2)]
    return header, rows
