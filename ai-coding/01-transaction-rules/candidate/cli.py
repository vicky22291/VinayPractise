"""Usage: python3 cli.py <transaction.json> <rules.json>"""
import logging
import sys

from radar.engine import evaluate
from radar.models import load_rules, load_transaction


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    print(evaluate(load_transaction(argv[1]), load_rules(argv[2])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
