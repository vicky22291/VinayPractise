import gc
import tracemalloc
import unittest

from kyc import summarize, validate_csv, validate_stream
from kyc_fixtures import GB, HEADER, US, codes, row


class CountingLines:
    def __init__(self, lines):
        self.lines = lines
        self.pulled = 0

    def __iter__(self):
        for line in self.lines:
            self.pulled += 1
            yield line


def generated(n, distinct=50):
    yield HEADER + "\r\n"
    for i in range(n):
        k = i % distinct
        yield f"r{i},Biz {i},{k:02d}-{k:07d},US,2020-01-01,Owner {i},o{k}@x.example\r\n"


class Part4Stream(unittest.TestCase):
    def test_lazy(self):
        src = CountingLines(generated(10_000))
        it = iter(validate_stream(src))
        first = next(it)
        self.assertEqual(first.line, 2)
        self.assertLessEqual(src.pulled, 5)
        next(it)
        self.assertLessEqual(src.pulled, 6)

    def test_lines_with_endings_blank_lines_and_bom(self):
        lines = ["﻿" + HEADER + "\r\n", US + "\r\n", "\r\n", GB + "\n"]
        results = list(validate_stream(lines))
        self.assertEqual([r.line for r in results], [2, 4])
        self.assertTrue(all(r.valid for r in results), [r.errors for r in results])

    def test_stream_matches_validate_csv(self):
        rows = [row("a"), "x,Short", row("b", country="ZZ"), row("c", tax_id="11-1111111")]
        text = "\n".join([HEADER, *rows]) + "\n"
        streamed = list(validate_stream(text.splitlines(keepends=True)))
        whole = validate_csv(text)
        self.assertEqual([(r.line, r.record_id, codes(r)) for r in streamed],
                         [(r.line, r.record_id, codes(r)) for r in whole])

    def test_summarize(self):
        rows = [
            row("a"),
            row("b"),
            row("c", country="ZZ", email="c@x.example"),
            "x,Short",
            row("d", tax_id="11-1111111", email="d@x.example"),
            row("e"),
        ]
        s = summarize(validate_stream(("\n".join([HEADER, *rows]) + "\n").splitlines(True)), top=2)
        self.assertEqual((s.total, s.valid, s.invalid), (6, 2, 4))
        self.assertEqual(s.top_codes, [("DUPLICATE_TAX_ID", 2), ("INVALID_COUNTRY", 1)])

    def test_summarize_ties_by_code(self):
        rows = [row("a", country="ZZ", email="a@x.example", tax_id="11-1111111"), "x,Short"]
        s = summarize(validate_csv("\n".join([HEADER, *rows])), top=5)
        self.assertEqual(s.top_codes, [("INVALID_COUNTRY", 1), ("WRONG_COLUMN_COUNT", 1)])

    def test_memory_does_not_grow_with_file(self):
        gc.collect()
        tracemalloc.start()
        try:
            s = summarize(validate_stream(generated(50_000)), top=3)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(s.total, 50_000)
        self.assertEqual(s.top_codes[0], ("DUPLICATE_TAX_ID", 49_950))
        self.assertLess(peak, 4 * 1024 * 1024, f"peak {peak / 1e6:.1f} MB")


if __name__ == "__main__":
    unittest.main()
