"""Multiply two matrices stored in binary files, in memory or out of core.

    multiply("a.bin", "b.bin", "c.bin")                      # float32/float64 picked from elem_size
    multiply("a.bin", "b.bin", "c.bin", fmt="i")             # int32
    multiply_tiled("a.bin", "b.bin", "c.bin", memory_budget=2**28)
"""

from .multiply import multiply, multiply_tiled, tile_side

__all__ = ["multiply", "multiply_tiled", "tile_side"]
