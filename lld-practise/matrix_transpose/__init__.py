"""Transpose a matrix stored in a binary file, in memory or out of core.

    transpose("m.bin")                              # writes m.transposed.bin
    transpose_tiled("big.bin", memory_budget=2**28) # 256 MiB of RAM, any file size
"""

from .transpose import tile_side, transpose, transpose_tiled

__all__ = ["tile_side", "transpose", "transpose_tiled"]
