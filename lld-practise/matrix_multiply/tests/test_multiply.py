"""Run from lld-practise/:  python3 -m unittest -v"""

import os
import random
import struct
import tempfile
import tracemalloc
import unittest

from binary_matrix import Header, read_matrix, write_matrix
from matrix_multiply import multiply, multiply_tiled, tile_side

# (M, K, N) shapes: vectors, ragged against tile=4, and an empty inner dimension.
SHAPES = [(1, 1, 1), (1, 5, 1), (5, 1, 5), (3, 4, 2), (7, 5, 6), (9, 9, 9), (4, 0, 3)]


def write_values(path: str, rows: int, cols: int, values: list, fmt: str = "d") -> None:
    elem_size = struct.calcsize(fmt)
    write_matrix(path, Header(rows, cols, elem_size), struct.pack(f"<{len(values)}{fmt}", *values))


def read_values(path: str, fmt: str = "d") -> tuple[Header, list]:
    header, data = read_matrix(path)
    return header, list(struct.unpack(f"<{header.rows * header.cols}{fmt}", data))


def reference(a: list, b: list, m: int, k: int, n: int) -> list:
    """Test oracle, written independently of the code under test."""
    rows = [a[i * k:(i + 1) * k] for i in range(m)]
    cols = [[b[r * n + j] for r in range(k)] for j in range(n)]
    return [sum(x * y for x, y in zip(row, col)) for row in rows for col in cols]


def small_ints(count: int, seed: int) -> list:
    # Integer-valued floats sum exactly, so tiled and simple must match bit for bit.
    rnd = random.Random(seed)
    return [float(rnd.randint(-9, 9)) for _ in range(count)]


class MultiplyContract:
    """Behaviour both versions must share. Mixed into one TestCase per version."""

    def run_multiply(self, a_name: str, b_name: str, out_name: str, fmt: str | None = None) -> str:
        raise NotImplementedError

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.a = os.path.join(tmp.name, "a.bin")
        self.b = os.path.join(tmp.name, "b.bin")
        self.c = os.path.join(tmp.name, "c.bin")

    def test_known_2x3_times_3x2(self):
        write_values(self.a, 2, 3, [1, 2, 3,
                                    4, 5, 6])
        write_values(self.b, 3, 2, [7, 8,
                                    9, 10,
                                    11, 12])
        self.run_multiply(self.a, self.b, self.c)
        self.assertEqual(read_values(self.c), (Header(2, 2, 8), [58.0, 64.0,
                                                                  139.0, 154.0]))

    def test_matches_reference_for_many_shapes(self):
        for m, k, n in SHAPES:
            with self.subTest(m=m, k=k, n=n):
                a, b = small_ints(m * k, seed=1), small_ints(k * n, seed=2)
                write_values(self.a, m, k, a)
                write_values(self.b, k, n, b)
                self.run_multiply(self.a, self.b, self.c)
                self.assertEqual(read_values(self.c), (Header(m, n, 8), reference(a, b, m, k, n)))

    def test_identity_leaves_matrix_unchanged(self):
        a = small_ints(5 * 5, seed=3)
        identity = [1.0 if i == j else 0.0 for i in range(5) for j in range(5)]
        write_values(self.a, 5, 5, a)
        write_values(self.b, 5, 5, identity)
        self.run_multiply(self.a, self.b, self.c)
        self.assertEqual(read_values(self.c)[1], a)

    def test_element_types(self):
        cases = [("f", [0.5, -1.25, 2.0, 3.75]), ("i", [-3, 7, 100, -2]), ("q", [2**31, -5, 1, 9])]
        for fmt, values in cases:
            with self.subTest(fmt=fmt):
                write_values(self.a, 2, 2, values, fmt)
                write_values(self.b, 2, 2, values, fmt)
                # Only float32 has a default for its elem_size, so pass fmt for the ints.
                self.run_multiply(self.a, self.b, self.c, fmt=None if fmt == "f" else fmt)
                self.assertEqual(read_values(self.c, fmt)[1], reference(values, values, 2, 2, 2))

    def test_int32_overflow_raises_instead_of_wrapping(self):
        write_values(self.a, 1, 1, [2**20], "i")
        write_values(self.b, 1, 1, [2**20], "i")
        with self.assertRaises(OverflowError):
            self.run_multiply(self.a, self.b, self.c, fmt="i")

    def test_rejects_bad_inputs(self):
        cases = {
            "inner dims differ": ((2, 3, "d"), (2, 2, "d"), None),
            "elem sizes differ": ((2, 2, "d"), (2, 2, "f"), None),
            "no default type for 2-byte elements": ((2, 2, "h"), (2, 2, "h"), None),
            "fmt size does not match elem_size": ((2, 2, "d"), (2, 2, "d"), "f"),
        }
        for label, ((ar, ac, af), (br, bc, bf), fmt) in cases.items():
            with self.subTest(label):
                write_values(self.a, ar, ac, [1] * (ar * ac), af)
                write_values(self.b, br, bc, [1] * (br * bc), bf)
                with self.assertRaises(ValueError):
                    self.run_multiply(self.a, self.b, self.c, fmt=fmt)


class InMemoryMultiplyTest(MultiplyContract, unittest.TestCase):
    def run_multiply(self, a_name, b_name, out_name, fmt=None):
        return multiply(a_name, b_name, out_name, fmt)


class TiledMultiplyTest(MultiplyContract, unittest.TestCase):
    # tile=4 forces several k-steps per output tile and ragged edge tiles.
    def run_multiply(self, a_name, b_name, out_name, fmt=None):
        return multiply_tiled(a_name, b_name, out_name, fmt, tile=4)

    def test_matches_in_memory_version_for_every_tile_size(self):
        m, k, n = 7, 5, 6
        write_values(self.a, m, k, small_ints(m * k, seed=4))
        write_values(self.b, k, n, small_ints(k * n, seed=5))
        expected = read_matrix(multiply(self.a, self.b, self.c + ".expected"))

        for tile in [1, 2, 3, 4, 5, 6, 7, 100]:
            with self.subTest(tile=tile):
                multiply_tiled(self.a, self.b, self.c, tile=tile)
                self.assertEqual(read_matrix(self.c), expected)

    def test_rejects_non_positive_tile(self):
        write_values(self.a, 2, 2, [1.0] * 4)
        write_values(self.b, 2, 2, [1.0] * 4)
        with self.assertRaises(ValueError):
            multiply_tiled(self.a, self.b, self.c, tile=0)

    def test_peak_memory_stays_within_budget(self):
        n = 96  # two 72 KiB float64 inputs
        budget = 24 * 1024
        write_values(self.a, n, n, small_ints(n * n, seed=6))
        write_values(self.b, n, n, small_ints(n * n, seed=7))

        tracemalloc.start()
        self.addCleanup(tracemalloc.stop)
        multiply_tiled(self.a, self.b, self.c, memory_budget=budget)
        _, peak = tracemalloc.get_traced_memory()

        self.assertLessEqual(peak, budget + 16 * 1024)  # slack: file objects, loop objects
        self.assertEqual(read_matrix(self.c)[0], Header(n, n, 8))


class TileSideTest(unittest.TestCase):
    def test_largest_square_where_a_b_and_accumulator_fit(self):
        for budget in [1024, 65536, 256 * 1024 * 1024]:
            for elem_size in [4, 8]:
                with self.subTest(budget=budget, elem_size=elem_size):
                    t = tile_side(budget, elem_size)
                    per_element = 2 * elem_size + 8
                    self.assertLessEqual(t * t * per_element, budget)
                    self.assertGreater((t + 1) * (t + 1) * per_element, budget)

    def test_never_below_one(self):
        self.assertEqual(tile_side(memory_budget=1, elem_size=8), 1)


if __name__ == "__main__":
    unittest.main()
