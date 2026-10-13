"""Run from lld-practise/:  python3 -m unittest -v"""

import os
import tempfile
import unittest

from binary_matrix import (
    HEADER_SIZE,
    Header,
    create_output,
    read_matrix,
    read_tile,
    write_matrix,
    write_tile,
)


class HeaderTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "m.bin")

    def test_is_20_bytes_and_round_trips(self):
        header = Header(rows=70_000, cols=3, elem_size=8)
        self.assertEqual(HEADER_SIZE, 20)
        self.assertEqual(len(header.pack()), HEADER_SIZE)
        with open(self.path, "wb") as f:
            f.write(header.pack())
        with open(self.path, "rb") as f:
            self.assertEqual(Header.read(f), header)

    def test_offset_is_row_major(self):
        header = Header(rows=3, cols=5, elem_size=4)
        self.assertEqual(header.offset(0, 0), HEADER_SIZE)
        self.assertEqual(header.offset(2, 1), HEADER_SIZE + (2 * 5 + 1) * 4)

    def test_write_matrix_rejects_wrong_data_length(self):
        with self.assertRaises(ValueError):
            write_matrix(self.path, Header(2, 2, 1), bytes(3))


class TileIOTest(unittest.TestCase):
    # 4 x 5 matrix of 1-byte elements, value = 10 * row + col.
    HEADER = Header(rows=4, cols=5, elem_size=1)
    DATA = bytes(10 * i + j for i in range(4) for j in range(5))

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, "m.bin")
        write_matrix(self.path, self.HEADER, self.DATA)

    def test_read_tile_returns_the_sub_block(self):
        with open(self.path, "rb", buffering=0) as f:
            block = read_tile(f, self.HEADER, r0=1, c0=2, h=2, w=3)
        self.assertEqual(block, bytes([12, 13, 14,
                                       22, 23, 24]))

    def test_read_tile_past_end_of_file_raises(self):
        with open(self.path, "rb", buffering=0) as f:
            with self.assertRaises(IOError):
                read_tile(f, self.HEADER, r0=3, c0=0, h=2, w=5)  # row 4 does not exist

    def test_write_tile_lands_in_place_and_leaves_the_rest_zero(self):
        out = self.path + ".out"
        with create_output(out, self.HEADER) as f:
            write_tile(f, self.HEADER, r0=2, c0=1, h=2, w=2, block=bytes([7, 8,
                                                                          9, 6]))
        header, data = read_matrix(out)
        self.assertEqual(header, self.HEADER)
        self.assertEqual(data, bytes([0, 0, 0, 0, 0,
                                      0, 0, 0, 0, 0,
                                      0, 7, 8, 0, 0,
                                      0, 9, 6, 0, 0]))


if __name__ == "__main__":
    unittest.main()
