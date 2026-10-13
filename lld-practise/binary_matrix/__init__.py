"""The binary matrix file format shared by matrix_transpose and matrix_multiply.

20-byte header (signature, rows, cols, elem_size), then row-major data.
"""

from .files import (
    check_data_size,
    create_output,
    read_checked_header,
    read_matrix,
    read_tile,
    write_matrix,
    write_tile,
)
from .header import HEADER_SIZE, SIGNATURE, Header

__all__ = [
    "HEADER_SIZE",
    "SIGNATURE",
    "Header",
    "check_data_size",
    "create_output",
    "read_checked_header",
    "read_matrix",
    "read_tile",
    "write_matrix",
    "write_tile",
]
