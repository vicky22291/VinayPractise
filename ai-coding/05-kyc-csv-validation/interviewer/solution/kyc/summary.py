"""Summarize results without keeping them."""
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    total: int
    valid: int
    invalid: int
    top_codes: list


def summarize(results, top=5):
    total = valid = 0
    counts = Counter()
    for r in results:
        total += 1
        if r.valid:
            valid += 1
        counts.update(e.code for e in r.errors)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return Summary(total, valid, total - valid, ranked[:top])
