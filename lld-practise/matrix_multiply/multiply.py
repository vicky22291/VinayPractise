"""Multiply two binary matrix files, in memory or tile by tile.

C = A x B where A is M x K, B is K x N and C is M x N. Every output value is a
row-by-column dot product, written by hand: no numpy, no matmul, no @.
"""

import math
import sys
from array import array

from binary_matrix import (
    Header,
    create_output,
    read_checked_header,
    read_matrix,
    read_tile,
    write_matrix,
    write_tile,
)

DEFAULT_MEMORY_BUDGET = 256 * 1024 * 1024  # 256 MiB

# The header has no type field, so elem_size picks the type unless fmt is given.
# Codes are the `array` / `memoryview` type codes: "i" int32, "q" int64, "f" float32, ...
DEFAULT_FORMATS = {4: "f", 8: "d"}
ACCUMULATOR_SIZE = 8  # partial sums are kept as float64 or int64


def multiply(a_name: str, b_name: str, out_name: str, fmt: str | None = None) -> str:
    """Simple version: load A and B, compute every C[i][j], write C. Needs A + B + C in RAM."""
    a_header, a_raw = read_matrix(a_name)
    b_header, b_raw = read_matrix(b_name)
    out_header, fmt = _plan(a_header, b_header, fmt)

    c = _zeros(fmt, out_header.rows * out_header.cols)
    _multiply_add(_view(a_raw, fmt), _view(b_raw, fmt), c, a_header.rows, a_header.cols, b_header.cols)
    write_matrix(out_name, out_header, _encode(c, fmt))
    return out_name


def multiply_tiled(
    a_name: str,
    b_name: str,
    out_name: str,
    fmt: str | None = None,
    memory_budget: int = DEFAULT_MEMORY_BUDGET,
    tile: int | None = None,
) -> str:
    """Out-of-core version: blocked matrix multiply, three tiles in RAM at a time.

    For each output tile C[i0, j0], walk k0 across the shared dimension, add
    A[i0, k0] x B[k0, j0] into an accumulator, then write the C tile exactly once.
    """
    with open(a_name, "rb", buffering=0) as fa, open(b_name, "rb", buffering=0) as fb:
        a_header, b_header = read_checked_header(fa), read_checked_header(fb)
        out_header, fmt = _plan(a_header, b_header, fmt)
        tile = tile if tile is not None else tile_side(memory_budget, a_header.elem_size)
        if tile < 1:
            raise ValueError(f"tile must be >= 1, got {tile}")
        m, inner, n = a_header.rows, a_header.cols, b_header.cols

        with create_output(out_name, out_header) as fc:
            for i0 in range(0, m, tile):
                h = min(tile, m - i0)
                for j0 in range(0, n, tile):
                    w = min(tile, n - j0)
                    c = _zeros(fmt, h * w)
                    for k0 in range(0, inner, tile):
                        d = min(tile, inner - k0)
                        a = _view(read_tile(fa, a_header, i0, k0, h, d), fmt)
                        b = _view(read_tile(fb, b_header, k0, j0, d, w), fmt)
                        _multiply_add(a, b, c, h, d, w)
                        # Free both before the next read, or 4 tiles are alive at once.
                        del a, b
                    write_tile(fc, out_header, i0, j0, h, w, _encode(c, fmt))
    return out_name


def tile_side(memory_budget: int, elem_size: int) -> int:
    """Largest square tile so an A tile, a B tile and the C accumulator fit the budget."""
    return max(1, math.isqrt(memory_budget // (2 * elem_size + ACCUMULATOR_SIZE)))


def _multiply_add(a, b, c, rows: int, inner: int, cols: int) -> None:
    """c (rows x cols) += a (rows x inner) times b (inner x cols). Flat row-major sequences.

    Each output value is one row-by-column dot product.
    """
    for i in range(rows):
        a_row = i * inner
        for j in range(cols):
            dot = 0
            for k in range(inner):
                dot += a[a_row + k] * b[k * cols + j]
            c[i * cols + j] += dot


def _plan(a: Header, b: Header, fmt: str | None) -> tuple[Header, str]:
    """Validate the pair and return the output header and element type code."""
    if a.cols != b.rows:
        raise ValueError(f"cannot multiply {a.rows}x{a.cols} by {b.rows}x{b.cols}")
    if a.elem_size != b.elem_size:
        raise ValueError(f"elem_size differs: {a.elem_size} vs {b.elem_size}")
    if fmt is None:
        if a.elem_size not in DEFAULT_FORMATS:
            raise ValueError(f"no default type for elem_size {a.elem_size}, pass fmt")
        fmt = DEFAULT_FORMATS[a.elem_size]
    if array(fmt).itemsize != a.elem_size:
        raise ValueError(f"fmt {fmt!r} is {array(fmt).itemsize} bytes, elem_size is {a.elem_size}")
    if sys.byteorder != "little":
        # memoryview.cast reads native order. On a big-endian host, decode with array + byteswap.
        raise NotImplementedError("files are little-endian, this host is big-endian")
    return Header(rows=a.rows, cols=b.cols, elem_size=a.elem_size), fmt


def _view(raw: bytes | bytearray, fmt: str) -> memoryview:
    """Zero-copy typed view: indexing returns numbers, no second buffer is allocated."""
    return memoryview(raw).cast(fmt)


def _zeros(fmt: str, n: int) -> array:
    return array("d" if fmt in "fd" else "q", bytes(n * ACCUMULATOR_SIZE))


def _encode(c: array, fmt: str) -> bytes:
    """Narrow the accumulator to the output type. Raises OverflowError if an int does not fit."""
    return array(fmt, c).tobytes()
