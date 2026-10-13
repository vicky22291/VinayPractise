"""Transpose a binary matrix file, in memory or tile by tile.

Elements are treated as opaque `elem_size`-byte strings, so the same code
works for int8, float32, float64 or any fixed-width record.
"""

import math
import os

from binary_matrix import (
    create_output,
    read_checked_header,
    read_matrix,
    read_tile,
    write_matrix,
    write_tile,
)

DEFAULT_MEMORY_BUDGET = 256 * 1024 * 1024  # 256 MiB


def transpose(name: str, out_name: str | None = None) -> str:
    """Simple version: load the whole matrix, transpose, write. Needs ~2x the data size in RAM."""
    out_name = out_name or _default_out_name(name)
    header, data = read_matrix(name)
    out = _transpose_block(data, header.rows, header.cols, header.elem_size)
    write_matrix(out_name, header.transposed(), out)
    return out_name


def transpose_tiled(
    name: str,
    out_name: str | None = None,
    memory_budget: int = DEFAULT_MEMORY_BUDGET,
    tile: int | None = None,
) -> str:
    """Out-of-core version: one tile x tile block in RAM at a time.

    Each tile is read as `tile` contiguous runs, transposed in memory, and
    written straight to its final place in the output as `tile` contiguous runs.
    """
    out_name = out_name or _default_out_name(name)
    with open(name, "rb", buffering=0) as src:
        header = read_checked_header(src)
        out_header = header.transposed()
        tile = tile if tile is not None else tile_side(memory_budget, header.elem_size)
        if tile < 1:
            raise ValueError(f"tile must be >= 1, got {tile}")

        with create_output(out_name, out_header) as dst:
            for r0 in range(0, header.rows, tile):
                h = min(tile, header.rows - r0)
                for c0 in range(0, header.cols, tile):
                    w = min(tile, header.cols - c0)
                    block = read_tile(src, header, r0, c0, h, w)
                    flipped = _transpose_block(block, h, w, header.elem_size)
                    # Input tile at (r0, c0) of size h x w lands at (c0, r0) as w x h.
                    write_tile(dst, out_header, c0, r0, w, h, flipped)
                    # Free both before the next read, or 3 tiles are alive at once.
                    del block, flipped
    return out_name


def tile_side(memory_budget: int, elem_size: int) -> int:
    """Largest square tile whose input and output buffers both fit the budget."""
    return max(1, math.isqrt(memory_budget // (2 * elem_size)))


def _transpose_block(data: bytes | bytearray, rows: int, cols: int, elem_size: int) -> bytearray:
    """Row-major rows x cols in, row-major cols x rows out. The only transpose logic."""
    out = bytearray(len(data))
    for i in range(rows):
        for j in range(cols):
            src = (i * cols + j) * elem_size
            dst = (j * rows + i) * elem_size
            out[dst:dst + elem_size] = data[src:src + elem_size]
    return out


def _default_out_name(name: str) -> str:
    root, ext = os.path.splitext(name)
    return f"{root}.transposed{ext}"
