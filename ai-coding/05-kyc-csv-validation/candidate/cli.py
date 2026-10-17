"""Validate a business verification CSV and print a report.

    python3 cli.py data/merchants.csv
    python3 cli.py data/merchants.csv --format json
    python3 cli.py data/merchants.csv --format errors-csv > queue.csv
    python3 cli.py --drops data/drops          newest file per bank
"""
import argparse
import sys

from kyc import HeaderError, validate_csv
from kyc.report import format_report, to_error_csv, to_json
from kyc.sources import latest_per_bank, list_drops

FORMATS = {"text": format_report, "json": to_json, "errors-csv": to_error_csv}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--drops", metavar="DIR", help="validate the newest file per bank in DIR")
    parser.add_argument("--format", choices=sorted(FORMATS), default="text")
    parser.add_argument("--allow-invalid", action="store_true", help="exit 0 even when records are invalid")
    args = parser.parse_args(argv)
    if bool(args.path) == bool(args.drops):
        parser.error("give a path or --drops, not both")
    paths = [d.path for d in latest_per_bank(list_drops(args.drops))] if args.drops else [args.path]

    status = 0
    for path in paths:
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        try:
            results = validate_csv(text)
        except HeaderError as e:
            print(f"{path}: {e}", file=sys.stderr)
            status = 2
            continue
        if len(paths) > 1:
            print(f"== {path}")
        print(FORMATS[args.format](results))
        if not args.allow_invalid and not all(r.valid for r in results):
            status = max(status, 1)
    return status


if __name__ == "__main__":
    sys.exit(main())
