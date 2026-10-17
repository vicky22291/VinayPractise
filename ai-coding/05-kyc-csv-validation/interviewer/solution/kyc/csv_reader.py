"""Read the verification CSV into a header and data rows, using the csv module."""
import csv
import io

from kyc.schema import COLUMNS


class HeaderError(ValueError):
    """The header row is missing a required column."""


def iter_rows(lines):
    """Return (header, rows) where rows lazily yields (line, values).

    lines is any iterable of text lines, with or without their line endings.
    Blank lines are skipped but still counted.
    """
    reader = csv.reader(lines)
    try:
        raw_header = next(reader)
    except StopIteration:
        raise HeaderError("empty file") from None
    if raw_header and raw_header[0].startswith("﻿"):
        raw_header[0] = raw_header[0][1:]
    header = [h.strip().lower() for h in raw_header]
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise HeaderError("missing columns: " + ", ".join(missing))

    def rows():
        for values in reader:
            if not any(v.strip() for v in values):
                continue
            yield reader.line_num, [v.strip() for v in values]

    return header, rows()


def read_rows(text):
    """Return (header, rows) with rows as a list of (line, values). Line 1 is the header."""
    header, rows = iter_rows(io.StringIO(text, newline=""))
    return header, list(rows)
