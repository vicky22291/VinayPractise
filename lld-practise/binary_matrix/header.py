"""The 20-byte file header: signature, rows, cols, bytes per element.

Assumed layout (confirm with the interviewer: field widths and byte order):

    offset 0   8 bytes   signature  b"MATRIX01"
    offset 8   uint32    rows       little endian
    offset 12  uint32    cols       little endian
    offset 16  uint32    elem_size  little endian

Matrix data follows in row-major order: element (i, j) starts at
HEADER_SIZE + (i * cols + j) * elem_size.
"""

import struct
from dataclasses import dataclass
from typing import BinaryIO

SIGNATURE = b"MATRIX01"
_LAYOUT = struct.Struct("<8sIII")
HEADER_SIZE = _LAYOUT.size  # 20


@dataclass(frozen=True)
class Header:
    rows: int
    cols: int
    elem_size: int

    @property
    def data_size(self) -> int:
        return self.rows * self.cols * self.elem_size

    def offset(self, i: int, j: int) -> int:
        """Byte offset of element (i, j) from the start of the file."""
        return HEADER_SIZE + (i * self.cols + j) * self.elem_size

    def transposed(self) -> "Header":
        return Header(rows=self.cols, cols=self.rows, elem_size=self.elem_size)

    def pack(self) -> bytes:
        return _LAYOUT.pack(SIGNATURE, self.rows, self.cols, self.elem_size)

    @classmethod
    def read(cls, f: BinaryIO) -> "Header":
        raw = f.read(HEADER_SIZE)
        if len(raw) != HEADER_SIZE:
            raise ValueError(f"file too short for a {HEADER_SIZE}-byte header")
        signature, rows, cols, elem_size = _LAYOUT.unpack(raw)
        if signature != SIGNATURE:
            raise ValueError(f"bad signature {signature!r}, expected {SIGNATURE!r}")
        if elem_size == 0:
            raise ValueError("elem_size must be > 0")
        return cls(rows=rows, cols=cols, elem_size=elem_size)
