"""Run the report on sample data and print how much database work it did.

    python3 -m payouts.cli --merchants 200 --transactions 20000 > report.csv
"""
import argparse
import sys
import time

from payouts import sample
from payouts.report import build_report
from payouts.store import Store

DAY = "2026-10-14"
ROUND_TRIP_MS = 1.5


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--merchants", type=int, default=200)
    ap.add_argument("--transactions", type=int, default=20_000)
    a = ap.parse_args(argv)
    ms = sample.merchants(a.merchants)
    store = Store(ms, sample.transactions(ms, a.transactions, DAY), sample.fx_rates(DAY))
    start = time.perf_counter()
    report = build_report(store, DAY)
    elapsed = time.perf_counter() - start
    sys.stdout.write(report)
    calls = store.total_calls()
    print(f"{calls} round trips (~{calls * ROUND_TRIP_MS / 1000 / 60:.1f} min in prod), "
          f"{elapsed:.2f} s CPU here, {dict(store.calls)}", file=sys.stderr)


if __name__ == "__main__":
    main()
