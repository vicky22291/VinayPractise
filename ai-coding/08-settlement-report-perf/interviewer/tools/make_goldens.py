"""Regenerate the golden reports with the STARTER code (the behaviour to preserve).

    python3 ai-coding/08-settlement-report-perf/interviewer/tools/make_goldens.py

Also prints how often per-transaction rounding differs from sum-then-round, so we
know the rounding trap is live in the golden data.
"""
import hashlib
import os
import sys
import time
from decimal import ROUND_HALF_EVEN, Decimal

KIT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(KIT, "candidate"))
sys.path.insert(0, os.path.join(KIT, "interviewer", "tests"))

import kit08_data as data  # noqa: E402
from payouts.report import build_report  # noqa: E402
from payouts.store import Store  # noqa: E402

FIX = os.path.join(KIT, "interviewer", "tests", "fixtures")


def golden(spec, name, digest_only=False):
    ms = data.merchants(spec["merchants"], spec["mseed"])
    txns = list(data.transactions(ms, spec["txns"], spec["tseed"], other_day=spec.get("other_day", True)))
    store = Store(ms, txns, data.fx_rates())
    t = time.perf_counter()
    out = build_report(store, data.DAY)
    print(f"{name}: {len(txns)} txns, {store.total_calls()} calls, {time.perf_counter() - t:.1f} s, {len(out.splitlines())} lines")
    if digest_only:  # big: keep only a digest in the repo
        with open(os.path.join(FIX, name), "w") as f:
            f.write(hashlib.sha256(out.encode("utf-8")).hexdigest() + "\n")
    else:
        with open(os.path.join(FIX, name), "w", newline="") as f:
            f.write(out)
    # How many lines would a sum-then-round rewrite get wrong?
    rates = {(r.base, r.quote): r.rate for r in data.fx_rates()}
    payout = {m.id: m.payout_currency for m in ms}
    sums, rounded = {}, {}
    for t in txns:
        if t.day != data.DAY or t.merchant_id not in payout or t.currency == payout[t.merchant_id]:
            continue
        k = (t.merchant_id, t.currency)
        net = t.amount - t.fee
        r = rates[(t.currency, payout[t.merchant_id])]
        sums[k] = sums.get(k, 0) + net
        rounded[k] = rounded.get(k, 0) + int((Decimal(net) * r).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    differ = sum(1 for k in sums if int((Decimal(sums[k]) * rates[(k[1], payout[k[0]])]).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)) != rounded[k])
    print(f"   sum-then-round would change {differ} of {len(sums)} converted lines")


if __name__ == "__main__":
    os.makedirs(FIX, exist_ok=True)
    golden(data.P1, "golden_p1.csv")
    golden(data.P2, "golden_p2.sha256", digest_only=True)
