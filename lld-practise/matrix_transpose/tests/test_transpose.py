"""Run from lld-practise/:  python3 -m unittest -v"""

import os
import random
import tempfile
import tracemalloc
import unittest

from binary_matrix import SIGNATURE, Header, read_matrix, write_matrix
from matrix_transpose import tile_side, transpose, transpose_tiled

SHAPES = [(1, 1), (1, 7), (7, 1), (5, 8), (16, 16), (13, 9)]
ELEM_SIZES = [1, 3, 4, 8]


def random_data(rows: int, cols: int, elem_size: int, seed: int = 7) -> bytes:
    return random.Random(seed).randbytes(rows * cols * elem_size)


def element(data: bytes, cols: int, elem_size: int, i: int, j: int) -> bytes:
    start = (i * cols + j) * elem_size
    return data[start:start + elem_size]


class TransposeContract:
    """Behaviour both versions must share. Mixed into one TestCase per version."""

    def run_transpose(self, name: str, out_name: str | None = None) -> str:
        raise NotImplementedError

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.src = os.path.join(self.dir, "m.bin")
        self.dst = os.path.join(self.dir, "out.bin")

    def test_known_2x3_matrix(self):
        write_matrix(self.src, Header(2, 3, 1), bytes([1, 2, 3,
                                                       4, 5, 6]))
        self.run_transpose(self.src, self.dst)
        header, data = read_matrix(self.dst)
        self.assertEqual(header, Header(rows=3, cols=2, elem_size=1))
        self.assertEqual(data, bytes([1, 4,
                                      2, 5,
                                      3, 6]))

    def test_every_element_moves_to_mirrored_position(self):
        for rows, cols in SHAPES:
            for elem_size in ELEM_SIZES:
                with self.subTest(rows=rows, cols=cols, elem_size=elem_size):
                    data = random_data(rows, cols, elem_size)
                    write_matrix(self.src, Header(rows, cols, elem_size), data)
                    self.run_transpose(self.src, self.dst)
                    header, out = read_matrix(self.dst)

                    self.assertEqual(header, Header(cols, rows, elem_size))
                    for i in range(rows):
                        for j in range(cols):
                            self.assertEqual(
                                element(out, rows, elem_size, j, i),
                                element(data, cols, elem_size, i, j),
                            )

    def test_transposing_twice_gives_the_original_file(self):
        write_matrix(self.src, Header(13, 9, 4), random_data(13, 9, 4))
        back = os.path.join(self.dir, "back.bin")
        self.run_transpose(self.src, self.dst)
        self.run_transpose(self.dst, back)
        with open(self.src, "rb") as a, open(back, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_output_keeps_the_signature(self):
        write_matrix(self.src, Header(2, 3, 1), bytes(6))
        self.run_transpose(self.src, self.dst)
        with open(self.dst, "rb") as f:
            self.assertEqual(f.read(len(SIGNATURE)), SIGNATURE)

    def test_empty_matrix(self):
        write_matrix(self.src, Header(0, 5, 4), b"")
        self.run_transpose(self.src, self.dst)
        self.assertEqual(read_matrix(self.dst), (Header(5, 0, 4), b""))

    def test_input_file_is_untouched(self):
        write_matrix(self.src, Header(5, 8, 4), random_data(5, 8, 4))
        with open(self.src, "rb") as f:
            before = f.read()
        self.run_transpose(self.src, self.dst)
        with open(self.src, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_default_output_name(self):
        write_matrix(self.src, Header(2, 3, 1), bytes(6))
        out = self.run_transpose(self.src)
        self.assertEqual(out, os.path.join(self.dir, "m.transposed.bin"))
        self.assertEqual(read_matrix(out)[0], Header(3, 2, 1))

    def test_rejects_malformed_files(self):
        good_header = Header(2, 3, 1).pack()
        cases = {
            "short header": good_header[:10],
            "bad signature": b"NOTAMTRX" + good_header[8:] + bytes(6),
            "zero elem_size": Header(2, 3, 0).pack() + bytes(6),
            "truncated data": good_header + bytes(5),
            "trailing data": good_header + bytes(7),
        }
        for label, content in cases.items():
            with self.subTest(label):
                with open(self.src, "wb") as f:
                    f.write(content)
                with self.assertRaises(ValueError):
                    self.run_transpose(self.src, self.dst)


class InMemoryTransposeTest(TransposeContract, unittest.TestCase):
    def run_transpose(self, name, out_name=None):
        return transpose(name, out_name)


class TiledTransposeTest(TransposeContract, unittest.TestCase):
    # tile=4 forces many tiles, including ragged ones at the right and bottom edges.
    def run_transpose(self, name, out_name=None):
        return transpose_tiled(name, out_name, tile=4)

    def test_matches_in_memory_version_for_every_tile_size(self):
        rows, cols, elem_size = 13, 9, 4
        write_matrix(self.src, Header(rows, cols, elem_size), random_data(rows, cols, elem_size))
        expected = read_matrix(transpose(self.src, os.path.join(self.dir, "expected.bin")))

        for tile in [1, 2, 3, 4, 8, 9, 13, 100]:
            with self.subTest(tile=tile):
                transpose_tiled(self.src, self.dst, tile=tile)
                self.assertEqual(read_matrix(self.dst), expected)

    def test_rejects_non_positive_tile(self):
        write_matrix(self.src, Header(2, 3, 1), bytes(6))
        with self.assertRaises(ValueError):
            transpose_tiled(self.src, self.dst, tile=0)

    def test_peak_memory_stays_within_budget(self):
        rows = cols = 512
        elem_size = 4  # 1 MiB of data
        budget = 64 * 1024
        write_matrix(self.src, Header(rows, cols, elem_size), random_data(rows, cols, elem_size))

        tracemalloc.start()
        self.addCleanup(tracemalloc.stop)
        transpose_tiled(self.src, self.dst, memory_budget=budget)
        _, peak = tracemalloc.get_traced_memory()

        self.assertLessEqual(peak, budget + 16 * 1024)  # slack: file buffers, loop objects
        self.assertEqual(read_matrix(self.dst)[0], Header(cols, rows, elem_size))


class TileSideTest(unittest.TestCase):
    def test_largest_square_whose_in_and_out_buffers_fit(self):
        for budget in [1024, 65536, 256 * 1024 * 1024]:
            for elem_size in ELEM_SIZES:
                with self.subTest(budget=budget, elem_size=elem_size):
                    t = tile_side(budget, elem_size)
                    self.assertLessEqual(2 * t * t * elem_size, budget)
                    self.assertGreater(2 * (t + 1) * (t + 1) * elem_size, budget)

    def test_never_below_one(self):
        self.assertEqual(tile_side(memory_budget=1, elem_size=8), 1)


if __name__ == "__main__":
    unittest.main()
