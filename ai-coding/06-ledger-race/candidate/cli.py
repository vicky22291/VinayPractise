"""Simulate a busy payout night and run finance's check.

    python3 cli.py [--accounts 20] [--transfers 5000] [--workers 16] [--watchdog 20]
"""
import argparse
import logging
import os
import random
import sys
import threading

from ledger import Ledger, run_batch
from ledger.reconcile import reconcile


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--accounts", type=int, default=20)
    p.add_argument("--transfers", type=int, default=5000)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--watchdog", type=float, default=20.0, help="seconds before a stuck batch is killed")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s %(message)s")
    sys.setswitchinterval(1e-5)  # busier than prod, to surface problems sooner

    rng = random.Random(a.seed)
    ledger = Ledger()
    ids = [f"acct_{i:03d}" for i in range(a.accounts)]
    for account_id in ids:
        ledger.open_account(account_id, balance=10_000)
    requests = []
    for _ in range(a.transfers):
        src, dst = rng.sample(ids, 2)
        requests.append({"src": src, "dst": dst, "amount": rng.randint(1, 3_000)})
    results = []
    job = threading.Thread(target=lambda: results.extend(run_batch(ledger, requests, workers=a.workers)), daemon=True)
    job.start()
    job.join(timeout=a.watchdog)
    if job.is_alive():
        # Same watchdog ops runs in prod: a stuck batch is killed, not waited on.
        print(f"payout batch stuck after {a.watchdog} s, killing it")
        sys.stdout.flush()
        os._exit(3)

    report = reconcile(ledger)
    print(f"{sum(r is not None for r in results)} of {len(results)} transfers done")
    print("reconcile:", "OK" if report.ok else "FAILED")
    for problem in report.problems[:10]:
        print("  " + problem)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
