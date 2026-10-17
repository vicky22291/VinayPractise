"""Usage: python3 cli.py <payments.txt> <invoices.txt> [--csv out.csv]"""
import sys

from recon.export import write_csv
from recon.matcher import match_all
from recon.parsing import parse_invoice, parse_payment, read_lines
from recon.report import format_match, summary


def main(argv):
    args = argv[1:]
    csv_path = None
    if "--csv" in args:
        i = args.index("--csv")
        csv_path = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        return 2
    payments = [parse_payment(line) for line in read_lines(args[0])]
    invoices = [parse_invoice(line) for line in read_lines(args[1])]
    matches = match_all(payments, invoices)
    for m in matches:
        print(format_match(m))
    print(summary(matches))
    if csv_path:
        write_csv(matches, csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
