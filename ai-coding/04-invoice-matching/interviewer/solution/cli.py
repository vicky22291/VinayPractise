"""Usage: python3 cli.py <payments.txt> <invoices.txt> [--csv out.csv] [--tolerance N]"""
import sys

from recon.export import write_csv
from recon.matcher import match_all
from recon.parsing import parse_invoice, parse_payment, read_lines
from recon.report import format_match, summary


def _pop_option(args, name):
    if name not in args:
        return None
    i = args.index(name)
    value = args[i + 1]
    del args[i:i + 2]
    return value


def main(argv):
    args = argv[1:]
    csv_path = _pop_option(args, "--csv")
    tolerance = int(_pop_option(args, "--tolerance") or 0)
    if len(args) != 2:
        print(__doc__)
        return 2
    payments = [parse_payment(line) for line in read_lines(args[0])]
    invoices = [parse_invoice(line) for line in read_lines(args[1])]
    matches = match_all(payments, invoices, tolerance)
    lines = [format_match(m) for m in matches]
    for line in lines:
        print(line)
    print(summary(lines))
    if csv_path:
        write_csv(matches, csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
