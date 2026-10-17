import hashlib
import time
import tracemalloc
import unittest
from pathlib import Path

import kit08_data as data
from payouts.report import build_report
from payouts.store import ArchiveStore, Store

FIX = Path(__file__).parent / "fixtures"
PEAK_BUDGET = 16 * 1024 * 1024  # bytes


class Part2(unittest.TestCase):
    def test_archive_day_byte_identical_and_flat_memory(self):
        spec = data.P2
        ms = data.merchants(spec["merchants"], spec["mseed"])
        store = ArchiveStore(ms, data.fx_rates(), lambda day: data.transactions(ms, spec["txns"], spec["tseed"], day, other_day=False))
        tracemalloc.start()
        start = time.perf_counter()
        out = build_report(store, data.DAY)
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        want = (FIX / "golden_p2.sha256").read_text().strip()
        self.assertEqual(hashlib.sha256(out.encode("utf-8")).hexdigest(), want,
                         "archive report differs from the original report for the same rows")
        self.assertLess(peak, PEAK_BUDGET, f"peak {peak / 2**20:.1f} MiB while streaming {spec['txns']} rows")
        self.assertEqual(store.rows_read, spec["txns"])
        self.assertLessEqual(store.total_calls(), 20, dict(store.calls))
        self.assertLess(elapsed, 60)

    def test_primary_store_over_list_limit(self):
        ms = data.merchants(300, 41)
        rows = list(data.transactions(ms, 120_000, 42, orphans=False, other_day=False))
        primary = build_report(Store(ms, rows, data.fx_rates()), data.DAY)
        archive = build_report(ArchiveStore(ms, data.fx_rates(), lambda day: iter(rows)), data.DAY)
        self.assertEqual(primary, archive)


if __name__ == "__main__":
    unittest.main()
